import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_interpretation import Confidence, InterpretationStatus, RiskLevel


class ValueBreakdown(BaseModel):
	"""Detailed metric from the AI interpretation."""

	metric: str
	value: str | float
	unit: str | None = None
	status: str | None = None


class AIInterpretationBase(BaseModel):
	"""Base schema for AI interpretation, used for both request and response models."""

	summary: str | None = None
	value_breakdown: list[ValueBreakdown] | None = None
	suggested_questions: list[str] | None = None
	risk_level: RiskLevel | None = None
	confidence: Confidence | None = None


class AIInterpretationCreate(AIInterpretationBase):
	"""Request schema for creating a new AI interpretation"""

	medical_case_id: uuid.UUID


class AIInterpretationUpdate(BaseModel):
	"""Schema for updating an AI interpretation."""

	summary: str | None = None
	value_breakdown: dict | None = None
	suggested_questions: dict | None = None
	risk_level: RiskLevel | None = None
	confidence: Confidence | None = None
	status: InterpretationStatus | None = None


class AIInterpretationResponse(AIInterpretationBase):
	"""Response schema for AI interpretation, includes all fields from the database model."""

	id: uuid.UUID
	medical_case_id: uuid.UUID
	status: InterpretationStatus
	generated_at: datetime

	model_config = ConfigDict(from_attributes=True)
