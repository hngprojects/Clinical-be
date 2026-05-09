from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MedicalCaseBase(BaseModel):
	status: str


class MedicalCaseCreate(MedicalCaseBase):
	"""Schema for creating a medical case."""

	user_id: UUID | None = None
	guest_session_id: str | None = None


class MedicalCaseUpdate(BaseModel):
	"""Schema for updating a medical case."""

	status: str | None = None
	completed_at: datetime | None = None


class MedicalCaseResponse(MedicalCaseBase):
	"""Response schema for a medical case."""

	id: UUID
	user_id: UUID | None = None
	guest_session_id: str | None = None
	created_at: datetime
	completed_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
