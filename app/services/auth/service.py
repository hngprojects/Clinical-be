from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.otp import OtpPurpose
from app.models.user import User, UserRole
from app.repositories.otp import OtpRepository
from app.repositories.user import UserRepository
from app.schemas.auth import SignupRequest
from app.services.auth.otp import (
	OtpVerificationError,
	create_otp_for_user,
	verify_otp_for_user,
)
from app.services.auth.tokens import create_access_token


async def signup_user(
	user_repo: UserRepository,
	otp_repo: OtpRepository,
	payload: SignupRequest,
) -> tuple[User, str]:
	"""Create an unverified user (with hashed password) and return an email-verification OTP.

	If a user already exists for the email:
	- and is verified → raises 409 Conflict.
	- and is NOT verified → reuses the row, refreshes the password, and re-sends OTP.
	"""
	email = payload.email.strip().lower()
	existing = await user_repo.get_by_email(email)

	if existing is not None:
		if existing.is_email_verified:
			raise ConflictError("An account with this email already exists.")
		existing.password_hash = hash_password(payload.password)
		existing.first_name = payload.first_name.strip()
		existing.last_name = payload.last_name.strip()
		user = existing
	else:
		try:
			user = User(
				email=email,
				first_name=payload.first_name.strip(),
				last_name=payload.last_name.strip(),
				password_hash=hash_password(payload.password),
				role=UserRole.PATIENT,
				is_email_verified=False,
				is_active=True,
			)
			user_repo.add(user)
			await user_repo.flush()
		except IntegrityError:
			await user_repo.rollback()
			user = await user_repo.get_by_email(email)
			if user is None or user.is_email_verified:
				raise ConflictError("An account with this email already exists.")
			user.password_hash = hash_password(payload.password)
			user.first_name = payload.first_name.strip()
			user.last_name = payload.last_name.strip()

	_, code = await create_otp_for_user(otp_repo, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION)
	await user_repo.commit()
	await user_repo.refresh(user)

	return user, code


async def authenticate_credentials(
	user_repo: UserRepository,
	*,
	email: str,
	password: str,
) -> tuple[User, str, int]:
	"""Verify email + password and return (user, access_token, ttl_seconds).

	Raises:
		NotFoundError: if the email is not registered.
		ForbiddenError: if the account is inactive or email is unverified.
		UnauthorizedError: if the password is wrong.
	"""
	user = await user_repo.get_by_email(email)
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
	await user_repo.commit()
	await user_repo.refresh(user)

	token, ttl_seconds = create_access_token(user.id)
	return user, token, ttl_seconds


async def authenticate_otp(
	user_repo: UserRepository,
	otp_repo: OtpRepository,
	*,
	email: str,
	code: str,
) -> tuple[User, str, int]:
	"""Verify an email-verification OTP and return (user, access_token, ttl_seconds).

	Flips `is_email_verified=True` on success.
	"""
	user = await user_repo.get_by_email(email)
	if user is None:
		raise UnauthorizedError("Invalid code.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")

	try:
		await verify_otp_for_user(otp_repo, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION, code=code)
	except OtpVerificationError as exc:
		await user_repo.commit()
		raise UnauthorizedError(str(exc)) from exc

	now = datetime.now(timezone.utc)
	user.is_email_verified = True
	user.last_login_at = now

	await user_repo.commit()
	await user_repo.refresh(user)

	token, ttl_seconds = create_access_token(user.id)
	return user, token, ttl_seconds


async def resend_otp(
	user_repo: UserRepository,
	otp_repo: OtpRepository,
	*,
	email: str,
) -> tuple[User, str]:
	"""Re-issue an email-verification OTP and return the code."""
	user = await user_repo.get_by_email(email)
	if user is None:
		raise NotFoundError("No account found for this email.")
	if not user.is_active:
		raise ForbiddenError("This account is disabled.")
	if user.is_email_verified:
		raise ConflictError("Email is already verified. Use login instead.")

	_, code = await create_otp_for_user(otp_repo, user_id=user.id, purpose=OtpPurpose.EMAIL_VERIFICATION)
	await user_repo.commit()
	await user_repo.refresh(user)

	return user, code


def otp_ttl_seconds() -> int:
	return get_settings().OTP_EXPIRES_MINUTES * 60
