from uuid import UUID

from sqlalchemy import select

from app.models.chat import Chat
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
	model = Chat

	async def list_by_case(
		self,
		medical_case_id: UUID,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[Chat]:
		result = await self._session.execute(
			select(Chat)
			.where(Chat.medical_case_id == medical_case_id)
			.order_by(Chat.sent_at.asc())
			.offset(offset)
			.limit(limit)
		)
		return list(result.scalars().all())

	async def list_by_user(
		self,
		user_id: UUID,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[Chat]:
		result = await self._session.execute(
			select(Chat).where(Chat.user_id == user_id).order_by(Chat.sent_at.desc()).offset(offset).limit(limit)
		)
		return list(result.scalars().all())
