import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationBase(BaseModel):
	"""Base schema for notifications."""

	type: NotificationType
	title: str
	message: dict | None = None
	data: dict | None = None
	medical_case_id: uuid.UUID | None = None


class NotificationCreate(NotificationBase):
	"""Request schema for creating a new notification."""

	user_id: uuid.UUID


class NotificationUpdate(BaseModel):
	"""Schema for updating a notification, currently only supports marking as read."""

	is_read: bool
	read_at: datetime | None = None


class NotificationResponse(NotificationBase):
	"""Response schema for notifications."""

	id: uuid.UUID
	user_id: uuid.UUID
	is_read: bool
	read_at: datetime | None = None
	created_at: datetime

	model_config = {"from_attributes": True}
