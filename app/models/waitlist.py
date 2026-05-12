import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Waitlist(Base):
	"""Model representing a user who has signed up for the waitlist."""

	__tablename__ = "waitlist"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
