from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import hash_password, verify_password
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
	"""Create an unverified user (with hashed password) and send an email-verification OTP.

	If a user already exists for the email:
	- and is verified → raises 409 Conflict.
	- and is NOT verified → reuses the row, refreshes the password, and re-sends OTP.
	"""
	email = payload.email.strip().lower()
	existing = await _get_user_by_email(session, email)

	if existing is not None:
		if existing.is_email_verified:
			raise ConflictError("An account with this email already exists.")
		# Unverified: allow re-signup (e.g. user forgot they signed up, or OTP expired)
		existing.password_hash = hash_password(payload.password)
		existing.first_name = payload.first_name.strip()
		existing.last_name = payload.last_name.strip()
		user = existing
	else:
		user = User(
			email=email,
			first_name=payload.first_name.strip(),
			last_name=payload.last_name.strip(),
			password_hash=hash_password(payload.password),
			role=UserRole.PATIENT,
			is_email_verified=False,
			is_active=True,
		)
		session.add(user)
		await session.flush()

	_, code = await create_otp_for_user(session, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION)
	await session.commit()
	await session.refresh(user)

	await send_otp_email(
		to_email=user.email,
		first_name=user.first_name or user.email.split("@")[0],
		code=code,
		purpose=OtpPurpose.EMAIL_VERIFICATION,
	)
	return user


async def authenticate_credentials(session: AsyncSession, *, email: str, password: str) -> tuple[User, str, int]:
	"""Verify email + password and return (user, access_token, ttl_seconds).

	Raises:
		NotFoundError: if the email is not registered.
		ForbiddenError: if the account is inactive or email is unverified.
		UnauthorizedError: if the password is wrong.
	"""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise NotFoundError("No account found for this email.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")
	if not user.is_email_verified:
		raise ForbiddenError("Email not verified. Check your inbox for the verification code we sent during signup.")
	if not user.password_hash or not verify_password(password, user.password_hash):
		raise UnauthorizedError("Incorrect email or password.")

	now = datetime.now(timezone.utc)
	user.last_login_at = now
	await session.commit()
	await session.refresh(user)

	token, ttl_seconds = create_access_token(user.id)
	return user, token, ttl_seconds


async def authenticate_otp(
	session: AsyncSession,
	*,
	email: str,
	code: str,
) -> tuple[User, str, int]:
	"""Verify an email-verification OTP and return (user, access_token, ttl_seconds).

	Flips `is_email_verified=True` on success.
	"""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise UnauthorizedError("Invalid code.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")

	try:
		# NOTE: verify_otp_for_user commits the `attempts` increment on failure
		# inside the same transaction — do not roll back after this call.
		await verify_otp_for_user(session, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION, code=code)
	except OtpVerificationError as exc:
		await session.commit()
		raise UnauthorizedError(str(exc)) from exc

	now = datetime.now(timezone.utc)
	user.is_email_verified = True
	user.last_login_at = now

	await session.commit()
	await session.refresh(user)

	token, ttl_seconds = create_access_token(user.id)
	return user, token, ttl_seconds


async def resend_otp(session: AsyncSession, *, email: str) -> User:
	"""Re-issue an email-verification OTP."""
	user = await _get_user_by_email(session, email)
	if user is None:
		raise NotFoundError("No account found for this email.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")
	if user.is_email_verified:
		raise ConflictError("Email is already verified. Use login instead.")

	_, code = await create_otp_for_user(session, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION)
	await session.commit()
	await session.refresh(user)

	await send_otp_email(
		to_email=user.email,
		first_name=user.first_name or user.email.split("@")[0],
		code=code,
		purpose=OtpPurpose.EMAIL_VERIFICATION,
	)
	return user


def otp_ttl_seconds() -> int:
	return settings.OTP_EXPIRES_MINUTES * 60
