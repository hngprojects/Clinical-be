import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.ai_interpretation import AIInterpretation
	from app.models.chat import Chat
	from app.models.lab_result import LabResult
	from app.models.notification import Notification
	from app.models.user import User


class MedicalCaseStatus(str, enum.Enum):
	"""Status of a medical case."""

	PENDING = "pending"
	PROCESSING = "processing"
	COMPLETE = "complete"
	FAILED = "failed"


class MedicalCase(Base):
	__tablename__ = "medical_cases"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
	)
	guest_session_id: Mapped[str | None] = mapped_column(String, nullable=True)
	status: Mapped[MedicalCaseStatus] = mapped_column(
		Enum(MedicalCaseStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	user: Mapped["User"] = relationship(back_populates="medical_cases")
	lab_results: Mapped[list["LabResult"]] = relationship(back_populates="medical_case")
	ai_interpretations: Mapped[list["AIInterpretation"]] = relationship(back_populates="medical_case")
	chats: Mapped[list["Chat"]] = relationship(back_populates="medical_case")
	notifications: Mapped[list["Notification"]] = relationship(back_populates="medical_case")
