from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
	"""Encapsulates all database operations for the User model."""

	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def get_by_id(self, user_id: UUID) -> User | None:
		return await self._session.get(User, user_id)

	async def get_by_email(self, email: str) -> User | None:
		normalized = email.strip().lower()
		result = await self._session.execute(select(User).where(User.email == normalized))
		return result.scalar_one_or_none()

	async def get_by_google_id(self, google_id: str) -> User | None:
		result = await self._session.execute(select(User).where(User.google_id == google_id))
		return result.scalar_one_or_none()

	def add(self, user: User) -> None:
		self._session.add(user)

	async def flush(self) -> None:
		await self._session.flush()

	async def commit(self) -> None:
		await self._session.commit()

	async def refresh(self, user: User) -> None:
		await self._session.refresh(user)

	async def rollback(self) -> None:
		await self._session.rollback()
