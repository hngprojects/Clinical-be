from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	email: EmailStr
	google_id: str | None = None
	name: str
	role: str
	is_email_verified: bool = False
	is_active: bool = True


class UserCreate(UserBase):
	password: str


class UserRead(UserBase):
	id: UUID
	created_at: datetime
	last_login_at: datetime | None = None
