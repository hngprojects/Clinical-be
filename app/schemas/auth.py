from pydantic import BaseModel, EmailStr


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ForgotPasswordResponse(BaseModel):
	message: str


class ResetPasswordRequest(BaseModel):
	token: str
	new_password: str


class ResetPasswordResponse(BaseModel):
	message: str
