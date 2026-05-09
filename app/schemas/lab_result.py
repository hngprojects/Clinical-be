from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.lab_result import OCRStatus


class FileObject(BaseModel):
	"""Represents an uploaded file."""

	name: str
	url: str


class LabResultBase(BaseModel):
	file: FileObject
	ocr_status: OCRStatus

	@field_validator("file", mode="before")
	@classmethod
	def parse_file(cls, v: Any) -> Any:
		if isinstance(v, dict):
			return FileObject(**v)
		return v


class LabResultCreate(LabResultBase):
	"""Schema for creating a lab result."""

	medical_case_id: UUID


class LabResultUpdate(BaseModel):
	"""Schema for updating a lab result after OCR processing."""

	ocr_status: OCRStatus | None = None
	extracted_values: dict[str, Any] | None = None
	ocr_completed_at: datetime | None = None


class LabResultResponse(LabResultBase):
	"""Response schema for a lab result."""

	id: UUID
	medical_case_id: UUID
	extracted_values: dict[str, Any] | None = None
	ocr_completed_at: datetime | None = None
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)
