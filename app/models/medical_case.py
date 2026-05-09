import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.lab_result import LabResult
	from app.models.user import User


class MedicalCase(Base):
	__tablename__ = "medical_case"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
	guest_session_id: Mapped[str] = mapped_column(String, nullable=False)
	status: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

	user: Mapped["User"] = relationship(back_populates="medical_cases")
	lab_results: Mapped[list["LabResult"]] = relationship(back_populates="medical_case")
