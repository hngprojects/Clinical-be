from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
	"""Shared CRUD operations every repository inherits.

	Sub-classes set ``model`` to the SQLAlchemy model they manage.
	"""

	model: type[ModelT]

	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def get_by_id(self, record_id: UUID) -> ModelT | None:
		return await self._session.get(self.model, record_id)

	async def list_all(self, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
		result = await self._session.execute(select(self.model).offset(offset).limit(limit))
		return list(result.scalars().all())

	def add(self, instance: ModelT) -> None:
		self._session.add(instance)

	async def delete(self, instance: ModelT) -> None:
		await self._session.delete(instance)
		await self._session.flush()

	async def flush(self) -> None:
		await self._session.flush()

	async def commit(self) -> None:
		await self._session.commit()

	async def refresh(self, instance: ModelT) -> None:
		await self._session.refresh(instance)

	async def rollback(self) -> None:
		await self._session.rollback()
