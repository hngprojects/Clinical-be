import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.medical_case import MedicalCase
	from app.models.user import User


class NotificationType(str, enum.Enum):
	"""Type of notification sent to the user."""

	INTERPRETATION_READY = "interpretation_ready"
	INTERPRETATION_FAILED = "interpretation_failed"


class Notification(Base):
	"""Model representing a notification sent to a user."""

	__tablename__ = "notification"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
	)
	medical_case_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), ForeignKey("medical_cases.id", ondelete="SET NULL"), nullable=True, index=True
	)
	type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
	title: Mapped[str] = mapped_column(String, nullable=False)
	message: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	user: Mapped["User"] = relationship(back_populates="notifications")
	medical_case: Mapped["MedicalCase"] = relationship(back_populates="notifications")
