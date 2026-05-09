from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.medical_case import MedicalCaseStatus


class MedicalCaseBase(BaseModel):
	status: MedicalCaseStatus


class MedicalCaseCreate(MedicalCaseBase):
	"""Schema for creating a medical case."""

	user_id: UUID | None = None
	guest_session_id: str | None = None


class MedicalCaseUpdate(BaseModel):
	"""Schema for updating a medical case."""

	status: MedicalCaseStatus | None = None
	completed_at: datetime | None = None


class MedicalCaseResponse(MedicalCaseBase):
	"""Response schema for a medical case."""

	id: UUID
	user_id: UUID | None = None
	guest_session_id: str | None = None
	created_at: datetime
	completed_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
