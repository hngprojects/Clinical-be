import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.chat import SenderType


class ChatBase(BaseModel):
    """Base schema for chat messages, used for both request and response models."""

    sender_type: SenderType
    content: dict
    medical_case_id: uuid.UUID


class ChatCreate(ChatBase):
    """Request schema for creating a new chat message."""

    user_id: uuid.UUID | None = None


class ChatResponse(ChatBase):
    """Response schema for chat messages, includes all fields from the database model."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)
