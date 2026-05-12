from pydantic import BaseModel, EmailStr


class ContactRequest(BaseModel):
	full_name: str
	email: EmailStr
	message: str
