import asyncio
from typing import Annotated
from urllib.parse import urlencode
from datetime import datetime, timezone 

from fastapi import APIRouter, Cookie, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, bearer_scheme
from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.responses import SuccessResponse
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
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
from app.services.auth.tokens import create_access_token, create_refresh_token, refresh_all_tokens, revoke_refresh_token, decode_access_token
from app.services.auth_service import (
	create_password_reset,
	reset_password,
)
from app.services.email import send_password_reset_email
from app.services.oauth import (
	exchange_google_code,
	fetch_google_user_info,
	get_or_create_google_user,
)

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
async def login(payload: LoginRequest, session: DBSession, response: Response) -> SuccessResponse[TokenResponse]:
	"""Authenticate with email + password. Returns a JWT on success.

	The account must have a verified email before login is permitted.
	"""
	user, access_token, ttl_seconds, refresh_token = await authenticate_credentials(
		session, email=payload.email, password=payload.password
	)
	settings = get_settings()

	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=settings.COOKIE_SAMESITE,
		max_age=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES * 60,
	)
	return SuccessResponse(
		message="Logged in successfully.",
		data=TokenResponse(
			access_token=access_token,
			token_type="bearer",
			expires_in=ttl_seconds,
			user=UserResponse.model_validate(user),
		),
	)


@router.post(
	"/verify-otp",
	response_model=SuccessResponse[TokenResponse],
)
async def verify_otp(
	payload: VerifyOtpRequest, session: DBSession, response: Response
) -> SuccessResponse[TokenResponse]:
	"""Verify the email-verification OTP sent after signup.

	Marks the email as verified and returns a JWT so the user is immediately
	logged in without needing a separate login step.
	"""
	user, access_token, ttl_seconds, refresh_token = await authenticate_otp(
		session,
		email=payload.email,
		code=payload.code,
	)
	settings = get_settings()
	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=settings.COOKIE_SAMESITE,
		max_age=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES * 60,
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
	"""
	user = await session.scalar(select(User).where(User.email == request.email.strip().lower()))
	if user:
		raw = await create_password_reset(session, user)
		# Commit the token to DB first, so the email contains a valid reference
		await session.commit()
		# Send the email in the background to mask the delay and mitigate enumeration
		asyncio.create_task(send_password_reset_email(user.email, raw))
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


@router.get("/google/callback", response_model=SuccessResponse[TokenResponse])
async def google_callback(
	code: str,
	session: DBSession,
	response: Response,
) -> SuccessResponse[TokenResponse]:
	"""Handle the Google OAuth callback and return app tokens."""
	token_data = await exchange_google_code(code)
	google_access_token = token_data.get("access_token")

	if not google_access_token:
		raise HTTPException(status_code=400, detail="Google access token not found")

	google_user = await fetch_google_user_info(google_access_token)
	user = await get_or_create_google_user(session, google_user)

	app_access_token, ttl_seconds = create_access_token(user.id)
	refresh_token = await create_refresh_token(user.id, session)
	settings = get_settings()
	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=settings.COOKIE_SAMESITE,
		max_age=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES * 60,
	)

	return SuccessResponse(
		message="Logged in successfully.",
		data=TokenResponse(
			access_token=app_access_token,
			token_type="bearer",
			expires_in=ttl_seconds,
			user=UserResponse.model_validate(user),
		),
	)


@router.post("/refresh-tokens", response_model=SuccessResponse[TokenResponse])
async def refresh(
	session: DBSession,
	response: Response,
	refresh_token: Annotated[str | None, Cookie()] = None,
) -> SuccessResponse[TokenResponse]:
	"""Refresh the access and refresh tokens."""
	if not refresh_token:
		raise UnauthorizedError(message="Refresh token cookie is required")
	tokens = await refresh_all_tokens(session=session, refresh_token=refresh_token)

	settings = get_settings()

	response.set_cookie(
		key="refresh_token",
		value=tokens["refresh_token"],
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=settings.COOKIE_SAMESITE,
		max_age=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES * 60,
	)
	return SuccessResponse(
		message="Tokens refreshed",
		data=TokenResponse(
			access_token=tokens["access_token"],
			token_type="bearer",
			expires_in=tokens["expires_in"],
		),
	)


@router.post("/logout", response_model=SuccessResponse)
async def logout(
	current_user: CurrentUser,
	session: DBSession,
	response: Response,
	credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
	refresh_token: Annotated[str | None, Cookie()] = None,
) -> SuccessResponse:
	"""
	Revoke both the access token and the refresh token in a single call.

	- The access token JTI is added to the blacklist table so any further
	  requests using it are rejected immediately, before natural expiry.
	- The refresh token (read from the httpOnly cookie) is marked as revoked
	  in the refresh_tokens table so it cannot be used to mint new tokens.
	- The refresh token cookie is cleared from the browser.
	"""
	# 1. Blacklist the access token
	if credentials:
		try:
			payload = decode_access_token(credentials.credentials)
			jti = payload.get("jti")
			exp = payload.get("exp")
			if jti and exp:
				blacklisted = TokenBlacklist(
					jti=jti,
					expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
				)
				session.add(blacklisted)
		except Exception:
			# Token already invalid — continue anyway, user is logging out
			pass

	# 2. Revoke the refresh token from the cookie
	if refresh_token:
		try:
			await revoke_refresh_token(refresh_token, session)
		except Exception:
			# Already revoked or not found — still fine
			pass

	await session.commit()

	# 3. Clear the refresh token cookie from the browser
	response.delete_cookie(key="refresh_token")

	return SuccessResponse(message="Logged out successfully.")
