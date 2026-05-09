from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class WaitlistCreate(BaseModel):
	"""Schema for joining the waitlist."""

	email: EmailStr


class WaitlistResponse(BaseModel):
	"""Response schema for a waitlist entry."""

	id: UUID
	email: EmailStr
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)
