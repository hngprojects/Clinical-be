import httpx

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.repositories.user import UserRepository

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def exchange_google_code(code: str) -> dict:
	"""Exchange an authorization code for Google tokens."""
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
		raise UnauthorizedError("Failed to exchange Google authorization code")

	return response.json()


async def fetch_google_user_info(access_token: str) -> dict:
	"""Fetch user profile from Google using an access token."""
	headers = {
		"Authorization": f"Bearer {access_token}",
	}

	async with httpx.AsyncClient() as client:
		response = await client.get(GOOGLE_USERINFO_URL, headers=headers)

	if response.status_code != 200:
		raise UnauthorizedError("Failed to fetch Google user information")

	return response.json()


async def get_or_create_google_user(
	user_repo: UserRepository,
	google_user: dict,
) -> User:
	"""Find or create a user from Google profile data."""
	google_id = google_user.get("sub")
	email = google_user.get("email")
	email_verified = google_user.get("email_verified", False)
	given_name = google_user.get("given_name") or ""
	family_name = google_user.get("family_name") or ""

	if not given_name:
		full = google_user.get("name") or email or ""
		parts = full.split(" ", 1)
		given_name = parts[0]
		family_name = parts[1] if len(parts) > 1 else given_name

	if not google_id or not email:
		raise UnauthorizedError("Google user profile is missing required fields")

	if not email_verified:
		raise UnauthorizedError("Google email address is not verified")

	# Check if user already exists by Google ID
	user = await user_repo.get_by_google_id(google_id)
	if user:
		user.email = email
		user.first_name = given_name
		user.last_name = family_name
		user.is_email_verified = True
		await user_repo.commit()
		await user_repo.refresh(user)
		return user

	# Check for email collision
	existing = await user_repo.get_by_email(email)
	if existing:
		raise ConflictError("An account with this email already exists")

	user = User(
		google_id=google_id,
		email=email,
		first_name=given_name,
		last_name=family_name,
		is_email_verified=True,
	)
	user_repo.add(user)
	await user_repo.commit()
	await user_repo.refresh(user)

	return user
