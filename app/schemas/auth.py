from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ResetPasswordRequest(BaseModel):
	token: str = Field(min_length=16, max_length=512)
	new_password: str = Field(min_length=8, max_length=72)


class GoogleAuthData(BaseModel):
	"""Response data for Google OAuth authentication."""

	access_token: str
	refresh_token: str
	token_type: str
	user: UserResponse
