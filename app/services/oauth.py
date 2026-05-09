import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def exchange_google_code(code: str) -> dict:
	payload = {
		"code": code,
		"client_id": settings.GOOGLE_CLIENT_ID,
		"client_secret": settings.GOOGLE_CLIENT_SECRET,
		"redirect_uri": settings.GOOGLE_REDIRECT_URI,
		"grant_type": "authorization_code",
	}

	async with httpx.AsyncClient() as client:
		response = await client.post(GOOGLE_TOKEN_URL, data=payload)

	if response.status_code != 200:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Failed to exchange Google authorization code",
		)

	return response.json()


async def fetch_google_user_info(access_token: str) -> dict:
	headers = {
		"Authorization": f"Bearer {access_token}",
	}

	async with httpx.AsyncClient() as client:
		response = await client.get(GOOGLE_USERINFO_URL, headers=headers)

	if response.status_code != 200:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Failed to fetch Google user information",
		)

	return response.json()


async def get_or_create_google_user(
	db: AsyncSession,
	google_user: dict,
) -> User:
	google_id = google_user.get("sub")
	email = google_user.get("email")
	email_verified = google_user.get("email_verified", False)
	name = google_user.get("name") or email

	if not google_id or not email:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Google user profile is missing required fields",
		)

	if not email_verified:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Google email address is not verified",
		)

	result = await db.execute(select(User).where(User.google_id == google_id))
	user = result.scalar_one_or_none()

	if user:
		user.email = email
		user.name = name
		user.is_email_verified = True
		await db.commit()
		await db.refresh(user)
		return user

	existing_email_result = await db.execute(select(User).where(User.email == email))
	existing_email_user = existing_email_result.scalar_one_or_none()

	if existing_email_user:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="An account with this email already exists",
		)

	user = User(
		google_id=google_id,
		email=email,
		name=name,
		is_email_verified=True,
	)

	db.add(user)
	await db.commit()
	await db.refresh(user)

	return user
