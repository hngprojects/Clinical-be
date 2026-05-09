from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.core.responses import SuccessResponse
from app.schemas.auth import (
	LoginRequest,
	OtpDispatchResponse,
	ResendOtpRequest,
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
			purpose="email_verification",  # type: ignore[arg-type]
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
			purpose="login",  # type: ignore[arg-type]
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
