from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TokenBlacklist(Base):
	"""
	Stores JTIs of revoked access tokens.

	Each row lives until the original token would have expired naturally.
	The purge_expired_tokens service cleans up stale rows periodically.
	"""

	__tablename__ = "token_blacklist"

	jti: Mapped[str] = mapped_column(String(36), primary_key=True)
	expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	blacklisted_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=lambda: datetime.now(timezone.utc),
	)