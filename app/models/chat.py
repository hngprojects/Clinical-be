import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SenderType(str, enum.Enum):
	"""Enum representing the type of sender in a chat message."""

	PATIENT = "patient"
	AI = "ai"


class Chat(Base):
	"""Model representing a chat conversation between a user and the system."""

	__tablename__ = "chat"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
	)
	sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
	content: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Storing message content as JSON for flexibility
	sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
	medical_case_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("medical_cases.id", ondelete="CASCADE"), nullable=False, index=True
	)
