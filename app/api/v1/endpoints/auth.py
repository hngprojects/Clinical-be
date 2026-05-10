from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.core.responses import SuccessResponse
from app.db.session import get_session
from app.models.otp import OtpPurpose
from app.models.user import User
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
	authenticate_otp,
	otp_ttl_seconds,
	resend_otp,
	signup_user,
	start_login,
)
from app.services.auth_service import (
	create_password_reset,
	delete_password_reset_by_raw_token,
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
	"""Register a new user and email them a verification OTP.

	Frontend sends `first_name`, `last_name`, `email`. The user is created in
	an unverified state; they must call `/auth/verify-otp` with the emailed
	code to activate the account.
	"""
	user = await signup_user(session, payload)
	return SuccessResponse(
		message="Verification code sent to your email.",
		data=OtpDispatchResponse(
			email=user.email,
			purpose=OtpPurpose.EMAIL_VERIFICATION,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


@router.post(
	"/login",
	response_model=SuccessResponse[OtpDispatchResponse],
)
async def login(payload: LoginRequest, session: DBSession) -> SuccessResponse[OtpDispatchResponse]:
	"""Step 1 of login: send an OTP to the user's email."""
	user = await start_login(session, email=payload.email)
	return SuccessResponse(
		message="Login code sent to your email.",
		data=OtpDispatchResponse(
			email=user.email,
			purpose=OtpPurpose.LOGIN,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


@router.post(
	"/verify-otp",
	response_model=SuccessResponse[TokenResponse],
)
async def verify_otp(payload: VerifyOtpRequest, session: DBSession) -> SuccessResponse[TokenResponse]:
	"""Step 2: verify the OTP. Marks email verified for signup, then issues a JWT."""
	user, access_token, ttl_seconds = await authenticate_otp(
		session,
		email=payload.email,
		code=payload.code,
		purpose=payload.purpose,
	)
	return SuccessResponse(
		message="Authenticated successfully.",
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
	"""Re-send an OTP for the given purpose (signup verification or login)."""
	user = await resend_otp(session, email=payload.email, purpose=payload.purpose)
	return SuccessResponse(
		message="A new code has been sent to your email.",
		data=OtpDispatchResponse(
			email=user.email,
			purpose=payload.purpose,
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
async def forgot_password(
	request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
) -> SuccessResponse:
	user = await session.scalar(select(User).where(User.email == request.email))
	if user:
		raw = await create_password_reset(session, user)
		await session.commit()
		try:
			send_password_reset_email(user.email, raw)
		except Exception:
			await delete_password_reset_by_raw_token(session, raw)
			await session.commit()
			raise
		return SuccessResponse(message="Password reset email sent successfully")
	else:
		raise NotFoundError("User not found")


@router.post(
	"/reset-password",
	response_model=SuccessResponse,
)
async def password_reset(
	request: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
) -> SuccessResponse:
	await reset_password(session, request.token, request.new_password)
	await session.commit()
	return SuccessResponse(message="Password reset successfully")
