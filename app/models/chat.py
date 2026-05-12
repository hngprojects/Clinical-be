import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.medical_case import MedicalCase
    from app.models.user import User


class SenderType(str, enum.Enum):
    """Enum representing the type of sender in a chat message."""

    PATIENT = "patient"
    AI = "ai"


class Chat(Base):
    """Model representing a chat conversation between a user and the system."""

    __tablename__ = "chat"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    medical_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[SenderType] = mapped_column(
        Enum(
            SenderType,
            name="sendertype",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    content: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # Storing message content as JSON for flexibility
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="chats")
    medical_case: Mapped["MedicalCase"] = relationship(back_populates="chats")
