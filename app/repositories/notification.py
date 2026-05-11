from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
	model = Notification

	async def list_by_user(
		self,
		user_id: UUID,
		*,
		unread_only: bool = False,
		offset: int = 0,
		limit: int = 50,
	) -> list[Notification]:
		stmt = (
			select(Notification)
			.where(Notification.user_id == user_id)
			.order_by(Notification.created_at.desc())
			.offset(offset)
			.limit(limit)
		)
		if unread_only:
			stmt = stmt.where(Notification.is_read.is_(False))
		result = await self._session.execute(stmt)
		return list(result.scalars().all())

	async def count_unread(self, user_id: UUID) -> int:
		result = await self._session.execute(
			select(func.count())
			.select_from(Notification)
			.where(Notification.user_id == user_id, Notification.is_read.is_(False))
		)
		return result.scalar_one()

	async def mark_read(self, notification_id: UUID) -> Notification | None:
		notif = await self.get_by_id(notification_id)
		if notif is None:
			return None
		notif.is_read = True
		notif.read_at = datetime.now(timezone.utc)
		return notif
