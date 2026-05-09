import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.chat import Chat
	from app.models.medical_case import MedicalCase
	from app.models.notification import Notification


class UserRole(str, enum.Enum):
	"""Role of the user in the system."""

	PATIENT = "patient"
	ADMIN = "admin"


class User(Base):
	__tablename__ = "users"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
	password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
	google_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
	name: Mapped[str] = mapped_column(String, nullable=False)
	role: Mapped[UserRole] = mapped_column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.PATIENT)
	is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	medical_cases: Mapped[list["MedicalCase"]] = relationship(back_populates="user")
	chats: Mapped[list["Chat"]] = relationship(back_populates="user")
	notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
