from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blocklist import TokenBlocklist


class TokenBlocklistRepository:
	"""Encapsulates all database operations for the TokenBlocklist model."""

	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def revoke(
		self,
		*,
		jti: str,
		user_id: UUID,
		expires_at: datetime,
	) -> None:
		entry = TokenBlocklist(jti=jti, user_id=user_id, expires_at=expires_at)
		self._session.add(entry)
		await self._session.commit()

	async def is_revoked(self, jti: str) -> bool:
		result = await self._session.execute(select(TokenBlocklist.id).where(TokenBlocklist.jti == jti).limit(1))
		return result.scalar_one_or_none() is not None
