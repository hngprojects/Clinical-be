from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.models.otp import OtpPurpose
from app.models.user import User, UserRole
from app.schemas.auth import SignupRequest
from app.services.auth.email import send_otp_email
from app.services.auth.otp import (
	OtpVerificationError,
	create_otp_for_user,
	verify_otp_for_user,
)
from app.services.auth.tokens import create_access_token


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
	normalized = email.strip().lower()
	result = await session.execute(select(User).where(User.email == normalized))
	return result.scalar_one_or_none()


async def signup_user(session: AsyncSession, payload: SignupRequest) -> User:
	"""Create an unverified user and send an email-verification OTP.

	If a user already exists for the email:
	- and is verified, raises 409 Conflict.
	- and is NOT verified, reuses the row, refreshes names, and re-sends OTP.
	"""
	email = payload.email.strip().lower()
	existing = await _get_user_by_email(session, email)

	if existing is not None:
		if existing.is_email_verified:
			raise ConflictError("An account with this email already exists.")
		existing.first_name = payload.first_name.strip()
		existing.last_name = payload.last_name.strip()
		user = existing
	else:
		user = User(
			email=email,
			first_name=payload.first_name.strip(),
			last_name=payload.last_name.strip(),
			role=UserRole.PATIENT,
			is_email_verified=False,
			is_active=True,
		)
		session.add(user)
		await session.flush()

	_, code = await create_otp_for_user(session, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION)
	await session.commit()
	await session.refresh(user)

	send_otp_email(
		to_email=user.email,
		first_name=user.first_name,
		code=code,
		purpose=OtpPurpose.EMAIL_VERIFICATION,
	)
	return user


async def start_login(session: AsyncSession, *, email: str) -> User:
	"""Issue a login OTP for an existing, verified user."""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise NotFoundError("No account found for this email.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")
	if not user.is_email_verified:
		raise ForbiddenError("Email not verified yet. Finish signup by entering the verification code we sent you.")

	_, code = await create_otp_for_user(session, user_id=user.id, purpose=OtpPurpose.LOGIN)
	await session.commit()
	await session.refresh(user)

	send_otp_email(
		to_email=user.email,
		first_name=user.first_name,
		code=code,
		purpose=OtpPurpose.LOGIN,
	)
	return user


async def authenticate_otp(
	session: AsyncSession,
	*,
	email: str,
	code: str,
	purpose: OtpPurpose,
) -> tuple[User, str, int]:
	"""Verify an OTP and return (user, access_token, ttl_seconds).

	For `EMAIL_VERIFICATION` purpose this also flips `is_email_verified=True`.
	"""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise UnauthorizedError("Invalid code.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")

	try:
		await verify_otp_for_user(session, user_id=user.id, purpose=purpose, code=code)
	except OtpVerificationError as exc:
		await session.commit()
		raise UnauthorizedError(str(exc)) from exc

	now = datetime.now(timezone.utc)
	if purpose is OtpPurpose.EMAIL_VERIFICATION:
		user.is_email_verified = True
	user.last_login_at = now

	await session.commit()
	await session.refresh(user)

	token, ttl_seconds = create_access_token(user.id)
	return user, token, ttl_seconds


async def resend_otp(
	session: AsyncSession,
	*,
	email: str,
	purpose: OtpPurpose,
) -> User:
	"""Re-issue an OTP for the given purpose."""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise NotFoundError("No account found for this email.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")

	if purpose is OtpPurpose.LOGIN and not user.is_email_verified:
		raise ForbiddenError("Email not verified yet. Finish signup by entering the verification code we sent you.")
	if purpose is OtpPurpose.EMAIL_VERIFICATION and user.is_email_verified:
		raise ConflictError("Email is already verified. Use login instead.")

	_, code = await create_otp_for_user(session, user_id=user.id, purpose=purpose)
	await session.commit()
	await session.refresh(user)

	send_otp_email(
		to_email=user.email,
		first_name=user.first_name,
		code=code,
		purpose=purpose,
	)
	return user


def otp_ttl_seconds() -> int:
	return settings.OTP_EXPIRES_MINUTES * 60
