from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, NotificationRepo
from app.core.responses import SuccessResponse
from app.schemas.notification import NotificationResponse
from app.services.notification import list_notifications, mark_as_read, unread_count

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
	"",
	response_model=SuccessResponse[list[NotificationResponse]],
)
async def list_mine(
	current_user: CurrentUser,
	notif_repo: NotificationRepo,
	unread_only: bool = Query(False),
	offset: int = Query(0, ge=0),
	limit: int = Query(50, ge=1, le=100),
) -> SuccessResponse[list[NotificationResponse]]:
	"""List notifications for the authenticated user."""
	notifs = await list_notifications(
		notif_repo,
		current_user.id,
		unread_only=unread_only,
		offset=offset,
		limit=limit,
	)
	return SuccessResponse(
		message="OK",
		data=[NotificationResponse.model_validate(n) for n in notifs],
	)


@router.get(
	"/unread-count",
	response_model=SuccessResponse[dict],
)
async def get_unread_count(
	current_user: CurrentUser,
	notif_repo: NotificationRepo,
) -> SuccessResponse[dict]:
	"""Return the number of unread notifications."""
	count = await unread_count(notif_repo, current_user.id)
	return SuccessResponse(message="OK", data={"unread": count})


@router.patch(
	"/{notification_id}/read",
	response_model=SuccessResponse[NotificationResponse],
)
async def read(
	notification_id: UUID,
	current_user: CurrentUser,
	notif_repo: NotificationRepo,
) -> SuccessResponse[NotificationResponse]:
	"""Mark a single notification as read."""
	notif = await mark_as_read(notif_repo, notification_id, user=current_user)
	return SuccessResponse(
		message="Notification marked as read.",
		data=NotificationResponse.model_validate(notif),
	)
