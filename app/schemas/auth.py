from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.user import UserResponse


class SignupRequest(BaseModel):
	"""Signup form: first name, last name, email, password + confirm.

	After account creation a 6-digit OTP is emailed for address verification.
	"""

	model_config = ConfigDict(str_strip_whitespace=True)

	first_name: str = Field(min_length=1, max_length=100)
	last_name: str = Field(min_length=1, max_length=100)
	email: EmailStr
	password: str = Field(min_length=8, max_length=72)
	confirm_password: str = Field(min_length=8, max_length=72)

	@model_validator(mode="after")
	def passwords_match(self) -> "SignupRequest":
		if self.password != self.confirm_password:
			raise ValueError("Passwords do not match.")
		return self


class LoginRequest(BaseModel):
	"""Login with email + password. Returns a JWT on success."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	password: str = Field(min_length=1, max_length=72)


class VerifyOtpRequest(BaseModel):
	"""Verify the email-verification OTP issued after signup."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	code: str = Field(min_length=4, max_length=12)


class ResendOtpRequest(BaseModel):
	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr


class TokenResponse(BaseModel):
	"""Returned after a successful login or OTP verification."""

	access_token: str
	token_type: str = "bearer"
	expires_in: int
	user: UserResponse | None = None

	model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
	user_id: str | None = None


class TokenPair(BaseModel):
	status: str = "success"
	access_token: str
	refresh_token: str
	token_type: str = "bearer"


class OtpDispatchResponse(BaseModel):
	"""Returned after an OTP is dispatched (signup or resend)."""

	email: EmailStr
	expires_in_seconds: int


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
