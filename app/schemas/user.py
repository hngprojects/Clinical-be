from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.PATIENT
    is_email_verified: bool = False
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user via email and password."""

    password: str


class GoogleUserCreate(UserBase):
    """Schema for creating a user via Google OAuth."""

    google_id: str


class UserUpdate(BaseModel):
    """Schema for updating a user profile."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Response schema for a user."""

    id: UUID
    google_id: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
