import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.medical_case import MedicalCase


class LabResult(Base):
	__tablename__ = "lab_results"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	medical_case_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("medical_cases.id", ondelete="CASCADE"), nullable=False, index=True
	)
	file: Mapped[Any] = mapped_column(JSONB, nullable=False)
	ocr_status: Mapped[str] = mapped_column(String, nullable=False)
	extracted_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
	ocr_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	medical_case: Mapped["MedicalCase"] = relationship(back_populates="lab_results")
