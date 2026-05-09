from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.medical_case import MedicalCaseStatus


class MedicalCaseBase(BaseModel):
	status: MedicalCaseStatus


class MedicalCaseCreate(MedicalCaseBase):
	"""Schema for creating a medical case."""

	user_id: UUID | None = None
	guest_session_id: str | None = None

	@model_validator(mode="after")
	def check_user_or_guest(self) -> "MedicalCaseCreate":
		if self.user_id is None and self.guest_session_id is None:
			raise ValueError("Either user_id or guest_session_id must be provided.")
		return self


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
