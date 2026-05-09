from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MedicalCaseBase(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	user_id: UUID
	guest_session_id: str
	status: str


class MedicalCaseCreate(MedicalCaseBase):
	pass


class MedicalCaseRead(MedicalCaseBase):
	id: UUID
	created_at: datetime
	completed_at: datetime | None = None
