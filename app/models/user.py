import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.medical_case import MedicalCase


class User(Base):
	__tablename__ = "user"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String, nullable=False)
	google_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
	name: Mapped[str] = mapped_column(String, nullable=False)
	role: Mapped[str] = mapped_column(String, nullable=False)
	is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	medical_cases: Mapped[list["MedicalCase"]] = relationship(back_populates="user")
