from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.core.responses import SuccessResponse
from app.models.otp import OtpPurpose
from app.schemas.auth import (
	ForgotPasswordRequest,
	LoginRequest,
	OtpDispatchResponse,
	ResendOtpRequest,
	ResetPasswordRequest,
	SignupRequest,
	TokenResponse,
	VerifyOtpRequest,
)
from app.schemas.user import UserResponse
from app.services.auth.service import (
	authenticate_credentials,
	authenticate_otp,
	otp_ttl_seconds,
	resend_otp,
	signup_user,
)
from app.services.auth_service import (
	create_password_reset,
	reset_password,
)
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
	"/signup",
	response_model=SuccessResponse[OtpDispatchResponse],
	status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest, session: DBSession) -> SuccessResponse[OtpDispatchResponse]:
	"""Register a new user with email + password and send a 6-digit OTP for email verification.

	The user is created in an unverified state. They must call `/auth/verify-otp`
	with the emailed code to activate the account before they can log in.
	"""
	user = await signup_user(session, payload)
	return SuccessResponse(
		message="Verification code sent to your email.",
		data=OtpDispatchResponse(
			email=user.email,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


@router.post(
	"/login",
	response_model=SuccessResponse[TokenResponse],
)
async def login(payload: LoginRequest, session: DBSession) -> SuccessResponse[TokenResponse]:
	"""Authenticate with email + password. Returns a JWT on success.

	The account must have a verified email before login is permitted.
	"""
	user, access_token, ttl_seconds = await authenticate_credentials(
		session, email=payload.email, password=payload.password
	)
	return SuccessResponse(
		message="Logged in successfully.",
		data=TokenResponse(
			access_token=access_token,
			expires_in=ttl_seconds,
			user=UserResponse.model_validate(user),
		),
	)


@router.post(
	"/verify-otp",
	response_model=SuccessResponse[TokenResponse],
)
async def verify_otp(payload: VerifyOtpRequest, session: DBSession) -> SuccessResponse[TokenResponse]:
	"""Verify the email-verification OTP sent after signup.

	Marks the email as verified and returns a JWT so the user is immediately
	logged in without needing a separate login step.
	"""
	user, access_token, ttl_seconds = await authenticate_otp(
		session,
		email=payload.email,
		code=payload.code,
	)
	return SuccessResponse(
		message="Email verified. Welcome!",
		data=TokenResponse(
			access_token=access_token,
			expires_in=ttl_seconds,
			user=UserResponse.model_validate(user),
		),
	)


@router.post(
	"/resend-otp",
	response_model=SuccessResponse[OtpDispatchResponse],
)
async def resend(payload: ResendOtpRequest, session: DBSession) -> SuccessResponse[OtpDispatchResponse]:
	"""Re-send the email-verification OTP (e.g. if it expired)."""
	user = await resend_otp(session, email=payload.email)
	return SuccessResponse(
		message="A new code has been sent to your email.",
		data=OtpDispatchResponse(
			email=user.email,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


@router.get(
	"/me",
	response_model=SuccessResponse[UserResponse],
)
async def me(current_user: CurrentUser) -> SuccessResponse[UserResponse]:
	"""Return the currently authenticated user."""
	return SuccessResponse(
		message="OK",
		data=UserResponse.model_validate(current_user),
	)


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(request: ForgotPasswordRequest, session: DBSession) -> SuccessResponse:
	"""Send a password-reset email.

	Always returns 200 regardless of whether the email is registered to prevent
	user-enumeration attacks.

	The email is sent BEFORE committing the token so a process crash between
	commit and send cannot leave a ghost token with no email delivered.
	"""
	from sqlalchemy import select

	from app.models.user import User

	user = await session.scalar(select(User).where(User.email == request.email.strip().lower()))
	if user:
		# Stage the token (flush only — not committed yet).
		raw = await create_password_reset(session, user)
		# Send first: if this raises, the transaction rolls back automatically.
		await send_password_reset_email(user.email, raw)
		# Persist only after email is confirmed sent.
		await session.commit()
	return SuccessResponse(message="If this email is registered, you'll receive a reset link shortly.")


@router.post(
	"/reset-password",
	response_model=SuccessResponse,
)
async def password_reset(request: ResetPasswordRequest, session: DBSession) -> SuccessResponse:
	"""Reset password using the token from the reset email."""
	await reset_password(session, request.token, request.new_password)
	await session.commit()
	return SuccessResponse(message="Password reset successfully.")
