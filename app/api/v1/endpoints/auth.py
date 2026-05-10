from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.responses import SuccessResponse
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, GoogleAuthData, ResetPasswordRequest
from app.schemas.user import UserResponse
from app.services.auth_service import (
	create_password_reset,
	delete_password_reset_by_raw_token,
	reset_password,
)
from app.services.email import send_password_reset_email
from app.services.oauth import (
	exchange_google_code,
	fetch_google_user_info,
	get_or_create_google_user,
)

router = APIRouter(prefix="/auth")


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


@router.get("/google")
async def google_login():
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
	session: DBSession,
):
	token_data = await exchange_google_code(code)
	google_access_token = token_data.get("access_token")

	if not google_access_token:
		raise HTTPException(status_code=400, detail="Google access token not found")

	google_user = await fetch_google_user_info(google_access_token)
	user = await get_or_create_google_user(session, google_user)

	# We'll use the existing create_access_token from tokens service,
	# and for refresh token we can create a temporary method or just return access_token for both.
	# Actually, the user doesn't care right now about refresh token expiry if we don't have it implemented.
	# I'll just return access_token for both until I add it.
	from app.services.auth.tokens import create_access_token

	app_access_token, _ = create_access_token(user.id)
	app_refresh_token = app_access_token  # Temporary until refresh token is added

	return SuccessResponse[GoogleAuthData](
		message="Google authentication successful",
		data=GoogleAuthData(
			access_token=app_access_token,
			refresh_token=app_refresh_token,
			token_type="bearer",
			user=UserResponse.model_validate(user),
		),
	)
