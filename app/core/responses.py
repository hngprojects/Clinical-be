from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper for all endpoints."""

    status: str = "success"
    message: str
    data: T | None = None


class ErrorDetail(BaseModel):
    """Represents a single field-level validation error."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response wrapper for all endpoints."""

    status: str = "error"
    message: str
    errors: list[ErrorDetail] | None = None
