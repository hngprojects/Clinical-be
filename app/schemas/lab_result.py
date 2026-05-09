from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LabResultBase(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	medical_case_id: UUID
	file: Any
	ocr_status: str
	extracted_data: dict[str, Any]
	ocr_completed_at: datetime | None = None


class LabResultCreate(LabResultBase):
	pass


class LabResultRead(LabResultBase):
	id: UUID
	created_at: datetime
