from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.otp import OtpPurpose
from app.schemas.user import UserResponse


class SignupRequest(BaseModel):
	"""Body sent by the signup form: first name, last name, email, and password."""

	model_config = ConfigDict(str_strip_whitespace=True)

	first_name: str = Field(min_length=1, max_length=100)
	last_name: str = Field(min_length=1, max_length=100)
	email: EmailStr
	password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
	"""Body sent by the login form: email and password."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	password: str = Field(min_length=8, max_length=72)


class VerifyOtpRequest(BaseModel):
	"""Verify the email-verification OTP sent after signup."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr
	code: str = Field(min_length=4, max_length=12)


class ResendOtpRequest(BaseModel):
	model_config = ConfigDict(str_strip_whitespace=True)

	email: EmailStr


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
