from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ResetPasswordRequest(BaseModel):
	token: str = Field(min_length=16, max_length=512)
	new_password: str = Field(min_length=8, max_length=72)
