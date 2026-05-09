from pydantic import BaseModel

from app.schemas.user import UserResponse


class GoogleAuthData(BaseModel):
	"""Response data for Google OAuth authentication."""

	access_token: str
	refresh_token: str
	token_type: str
	user: UserResponse
