from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.otp import OtpPurpose
from app.schemas.user import UserResponse


class SignupRequest(BaseModel):
	"""Body sent by the signup form: first name, last name, email."""

	model_config = ConfigDict(str_strip_whitespace=True)

	first_name: str = Field(min_length=1, max_length=100)
	last_name: str = Field(min_length=1, max_length=100)
	email: EmailStr


class LoginRequest(BaseModel):
	"""Step 1 of login: ask for an OTP to be sent to the user's email."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr


class VerifyOtpRequest(BaseModel):
	"""Step 2: verify the OTP. `purpose` decides whether this completes
	signup (email verification) or login."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	code: str = Field(min_length=4, max_length=12)
	purpose: OtpPurpose


class ResendOtpRequest(BaseModel):
	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	purpose: OtpPurpose


class TokenResponse(BaseModel):
	"""Returned after a successful OTP verification."""

	access_token: str
	token_type: str = "bearer"
	expires_in: int
	user: UserResponse

	model_config = ConfigDict(from_attributes=True)


class OtpDispatchResponse(BaseModel):
	"""Returned after an OTP is dispatched (signup, login, resend)."""

	email: EmailStr
	purpose: OtpPurpose
	expires_in_seconds: int


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ResetPasswordRequest(BaseModel):
	token: str = Field(min_length=16, max_length=512)
	new_password: str = Field(min_length=8, max_length=72)
