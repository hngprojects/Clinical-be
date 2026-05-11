import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TokenBlocklist(Base):
	"""Stores revoked JWT IDs so that logged-out tokens are rejected by the auth guard.

	A token whose `jti` appears here is treated as invalid regardless of its
	intrinsic `exp` claim.  Rows may be safely purged once `expires_at` is in
	the past — expired tokens are cryptographically invalid anyway.
	"""

	__tablename__ = "token_blocklist"

	# Partial index on expires_at so a future cleanup job can efficiently
	# delete rows whose natural expiry has already passed.
	__table_args__ = (Index("ix_token_blocklist_expires_at", "expires_at"),)

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
	)
	jti: Mapped[str] = mapped_column(
		String(36), nullable=False, unique=True, index=True
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
	)
	expires_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=lambda: datetime.now(timezone.utc),
	)
