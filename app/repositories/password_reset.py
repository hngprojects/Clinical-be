from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import PasswordResetToken


class PasswordResetRepository:
	"""Encapsulates all database operations for the PasswordResetToken model."""

	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def delete_all_for_user(self, user_id: UUID) -> None:
		await self._session.execute(
			delete(PasswordResetToken).where(
				PasswordResetToken.user_id == user_id,
			)
		)

	def add(self, token: PasswordResetToken) -> None:
		self._session.add(token)

	async def flush(self) -> None:
		await self._session.flush()

	async def get_by_token_hash(
		self,
		token_hash: str,
		*,
		lock: bool = False,
	) -> PasswordResetToken | None:
		stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
		if lock:
			stmt = stmt.with_for_update()
		return await self._session.scalar(stmt)

	async def delete(self, token: PasswordResetToken) -> None:
		await self._session.delete(token)
		await self._session.flush()
