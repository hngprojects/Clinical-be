import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.medical_case import MedicalCase


class RiskLevel(str, enum.Enum):
	"""Risk level of the medical case based on AI interpretation."""

	LOW = "low"
	MODERATE = "moderate"
	HIGH = "high"


class Confidence(str, enum.Enum):
	"""Confidence level of the AI interpretation."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"


class InterpretationStatus(str, enum.Enum):
	"""Status of the AI interpretation process."""

	PENDING = "pending"
	PROCESSING = "processing"
	COMPLETE = "complete"
	FAILED = "failed"


class AIInterpretation(Base):
	"""Model representing the AI interpretation of a medical case."""

	__tablename__ = "ai_interpretation"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	medical_case_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("medical_cases.id", ondelete="CASCADE"), nullable=False, index=True
	)
	summary: Mapped[str | None] = mapped_column(String, nullable=True)
	value_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	suggested_questions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	risk_level: Mapped[RiskLevel | None] = mapped_column(Enum(RiskLevel, name="risklevel", values_callable=lambda obj: [e.value for e in obj]), nullable=True)
	confidence: Mapped[Confidence | None] = mapped_column(Enum(Confidence, name="confidence", values_callable=lambda obj: [e.value for e in obj]), nullable=True)
	status: Mapped[InterpretationStatus] = mapped_column(
		Enum(InterpretationStatus, name="interpretationstatus", values_callable=lambda obj: [e.value for e in obj]), default=InterpretationStatus.PENDING, nullable=False
	)
	generated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	medical_case: Mapped["MedicalCase"] = relationship(back_populates="ai_interpretations")
