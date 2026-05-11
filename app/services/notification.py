from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationCreate


async def create_notification(
	notif_repo: NotificationRepository,
	payload: NotificationCreate,
) -> Notification:
	"""Create a notification for a user."""
	notif = Notification(
		user_id=payload.user_id,
		medical_case_id=payload.medical_case_id,
		type=payload.type,
		title=payload.title,
		message=payload.message,
		data=payload.data,
	)
	notif_repo.add(notif)
	await notif_repo.commit()
	await notif_repo.refresh(notif)
	return notif


async def list_notifications(
	notif_repo: NotificationRepository,
	user_id: UUID,
	*,
	unread_only: bool = False,
	offset: int = 0,
	limit: int = 50,
) -> list[Notification]:
	return await notif_repo.list_by_user(
		user_id,
		unread_only=unread_only,
		offset=offset,
		limit=limit,
	)


async def unread_count(
	notif_repo: NotificationRepository,
	user_id: UUID,
) -> int:
	return await notif_repo.count_unread(user_id)


async def mark_as_read(
	notif_repo: NotificationRepository,
	notification_id: UUID,
	*,
	user: User,
) -> Notification:
	"""Mark a single notification as read, enforcing ownership."""
	notif = await notif_repo.get_by_id(notification_id)
	if notif is None:
		raise NotFoundError("Notification not found.")
	if notif.user_id != user.id:
		raise ForbiddenError("You do not own this notification.")
	await notif_repo.mark_read(notification_id)
	await notif_repo.commit()
	await notif_repo.refresh(notif)
	return notif
