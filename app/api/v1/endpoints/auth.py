from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_session
from app.models.user import User
from app.services.oauth import (
	exchange_google_code,
	fetch_google_user_info,
	get_or_create_google_user,
)

router = APIRouter()


@router.get("/google")
async def google_login():
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


@router.get("/google/callback")
async def google_callback(
	code: str,
	db: AsyncSession = Depends(get_session),
):
	token_data = await exchange_google_code(code)

	google_access_token = token_data.get("access_token")

	if not google_access_token:
		raise HTTPException(
			status_code=400,
			detail="Google access token not found",
		)

	google_user = await fetch_google_user_info(google_access_token)

	user = await get_or_create_google_user(
		db,
		google_user,
	)

	app_access_token = create_access_token(subject=str(user.id))
	app_refresh_token = create_refresh_token(subject=str(user.id))

	return {
		"message": "Google authentication successful",
		"access_token": app_access_token,
		"refresh_token": app_refresh_token,
		"token_type": "bearer",
		"user": {
			"id": str(user.id),
			"email": user.email,
			"name": user.name,
			"is_email_verified": user.is_email_verified,
			"role": user.role.value,
		},
	}


@router.get("/me")
async def get_me(
	current_user: User = Depends(get_current_user),
):
	return {
		"id": str(current_user.id),
		"email": current_user.email,
		"name": current_user.name,
		"is_email_verified": current_user.is_email_verified,
		"role": current_user.role.value,
	}
