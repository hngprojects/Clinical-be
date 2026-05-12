import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def exchange_google_code(code: str) -> dict:
    settings = get_settings()
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
    given_name = google_user.get("given_name") or ""
    family_name = google_user.get("family_name") or ""
    # Fallback: split name if given_name/family_name not provided
    if not given_name:
        full = google_user.get("name") or email or ""
        parts = full.split(" ", 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else given_name

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
        user.first_name = given_name
        user.last_name = family_name
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
        first_name=given_name,
        last_name=family_name,
        is_email_verified=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
