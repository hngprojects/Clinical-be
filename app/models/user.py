from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
	name: Mapped[str | None] = mapped_column(String(255), nullable=True)
	picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
	email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
