import logging
from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import (
	CurrentUser,
	DBSession,
	OtpRepo,
	PasswordResetRepo,
	TokenBlocklistRepo,
	UserRepo,
	bearer_scheme,
)
from app.core.config import get_settings
from app.core.responses import SuccessResponse
from app.models.otp import OtpPurpose
from app.schemas.auth import (
	ForgotPasswordRequest,
	GoogleAuthData,
	LoginRequest,
	OtpDispatchResponse,
	ResendOtpRequest,
	ResetPasswordRequest,
	SignupRequest,
	TokenResponse,
	VerifyOtpRequest,
)
from app.schemas.user import UserResponse
from app.services.auth.blocklist import revoke_token
from app.services.auth.service import (
	authenticate_credentials,
	authenticate_otp,
	otp_ttl_seconds,
	resend_otp,
	signup_user,
)
from app.services.auth.tokens import create_access_token, decode_access_token
from app.services.auth_service import (
	create_password_reset,
	reset_password,
)
from app.services.oauth import (
	exchange_google_code,
	fetch_google_user_info,
	get_or_create_google_user,
)
from app.tasks.email import send_otp_email_task, send_password_reset_email_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _mask_email(email: str) -> str:
	if "@" in email:
		local, domain = email.split("@", 1)
		return f"{local[:2]}***@{domain}"
	return "***"


# Signup
@router.post(
	"/signup",
	response_model=SuccessResponse[OtpDispatchResponse],
	status_code=status.HTTP_201_CREATED,
)
async def signup(
	payload: SignupRequest,
	user_repo: UserRepo,
	otp_repo: OtpRepo,
) -> SuccessResponse[OtpDispatchResponse]:
	"""Register a new user and send a 6-digit OTP for email verification."""
	user, code = await signup_user(user_repo, otp_repo, payload)
	email_dispatched = False
	try:
		send_otp_email_task.delay(
			to_email=user.email,
			first_name=user.first_name or user.email.split("@")[0],
			code=code,
			purpose=OtpPurpose.EMAIL_VERIFICATION.value,
		)
		email_dispatched = True
	except Exception:
		logger.exception("Failed to enqueue OTP email for %s", _mask_email(user.email))
	return SuccessResponse(
		message=(
			"Verification code sent to your email."
			if email_dispatched
			else "Verification code created. If you do not receive an email, request a new code."
		),
		data=OtpDispatchResponse(
			email=user.email,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


# Login
@router.post(
	"/login",
	response_model=SuccessResponse[TokenResponse],
)
async def login(
	payload: LoginRequest,
	user_repo: UserRepo,
) -> SuccessResponse[TokenResponse]:
	"""Authenticate with email + password. Returns a JWT on success."""
	user, access_token, ttl_seconds = await authenticate_credentials(
		user_repo, email=payload.email, password=payload.password
	)
	return SuccessResponse(
		message="Logged in successfully.",
		data=TokenResponse(
			access_token=access_token,
			expires_in=ttl_seconds,
			user=UserResponse.model_validate(user),
		),
	)


# OTP verification & resend
@router.post(
	"/verify-otp",
	response_model=SuccessResponse[TokenResponse],
)
async def verify_otp(
	payload: VerifyOtpRequest,
	user_repo: UserRepo,
	otp_repo: OtpRepo,
) -> SuccessResponse[TokenResponse]:
	"""Verify the email-verification OTP sent after signup."""
	user, access_token, ttl_seconds = await authenticate_otp(
		user_repo,
		otp_repo,
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
async def resend(
	payload: ResendOtpRequest,
	user_repo: UserRepo,
	otp_repo: OtpRepo,
) -> SuccessResponse[OtpDispatchResponse]:
	"""Re-send the email-verification OTP."""
	user, code = await resend_otp(user_repo, otp_repo, email=payload.email)
	email_dispatched = False
	try:
		send_otp_email_task.delay(
			to_email=user.email,
			first_name=user.first_name or user.email.split("@")[0],
			code=code,
			purpose=OtpPurpose.EMAIL_VERIFICATION.value,
		)
		email_dispatched = True
	except Exception:
		logger.exception("Failed to enqueue OTP email for %s", _mask_email(user.email))
	return SuccessResponse(
		message=(
			"A new code has been sent to your email."
			if email_dispatched
			else "A new code was created. If you do not receive an email, request another code."
		),
		data=OtpDispatchResponse(
			email=user.email,
			expires_in_seconds=otp_ttl_seconds(),
		),
	)


# Current user
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


# Password reset
@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
	request: ForgotPasswordRequest,
	user_repo: UserRepo,
	reset_repo: PasswordResetRepo,
	session: DBSession,
) -> SuccessResponse:
	"""Send a password-reset email. Always returns 200 to prevent user enumeration."""
	user = await user_repo.get_by_email(request.email.strip().lower())
	if user:
		raw = await create_password_reset(reset_repo, user)
		await session.commit()
		try:
			send_password_reset_email_task.delay(user.email, raw)
		except Exception:
			logger.exception("Failed to enqueue password reset email for %s", _mask_email(user.email))
	return SuccessResponse(message="If this email is registered, you'll receive a reset link shortly.")


@router.post(
	"/reset-password",
	response_model=SuccessResponse,
)
async def password_reset(
	request: ResetPasswordRequest,
	reset_repo: PasswordResetRepo,
	user_repo: UserRepo,
	session: DBSession,
) -> SuccessResponse:
	"""Reset password using the token from the reset email."""
	await reset_password(reset_repo, user_repo, request.token, request.new_password)
	await session.commit()
	return SuccessResponse(message="Password reset successfully.")


# Logout
@router.post(
	"/logout",
	response_model=SuccessResponse,
	status_code=status.HTTP_200_OK,
)
async def logout(
	current_user: CurrentUser,
	blocklist_repo: TokenBlocklistRepo,
	credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> SuccessResponse:
	"""Revoke the current access token."""
	payload = decode_access_token(credentials.credentials)
	jti: str = payload["jti"]
	expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
	await revoke_token(blocklist_repo, jti=jti, user_id=current_user.id, expires_at=expires_at)
	return SuccessResponse(message="Logged out successfully.")


# Google OAuth
@router.get("/google")
async def google_login() -> RedirectResponse:
	"""Redirect to Google's OAuth consent screen."""
	settings = get_settings()
	query_params = urlencode(
		{
			"client_id": settings.GOOGLE_CLIENT_ID,
			"redirect_uri": settings.GOOGLE_REDIRECT_URI,
			"response_type": "code",
			"scope": "openid email profile",
		}
	)
	google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_params}"
	return RedirectResponse(url=google_auth_url)


@router.get("/google/callback", response_model=SuccessResponse[GoogleAuthData])
async def google_callback(
	code: str,
	user_repo: UserRepo,
) -> SuccessResponse[GoogleAuthData]:
	"""Handle the Google OAuth callback and return app tokens."""
	token_data = await exchange_google_code(code)
	google_access_token = token_data.get("access_token")

	if not google_access_token:
		from app.core.exceptions import UnauthorizedError

		raise UnauthorizedError("Google access token not found")

	google_user = await fetch_google_user_info(google_access_token)
	user = await get_or_create_google_user(user_repo, google_user)

	app_access_token, ttl_seconds = create_access_token(user.id)

	return SuccessResponse[GoogleAuthData](
		message="Google authentication successful",
		data=GoogleAuthData(
			access_token=app_access_token,
			refresh_token=app_access_token,
			token_type="bearer",
			user=UserResponse.model_validate(user),
		),
	)
