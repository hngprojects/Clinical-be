import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class EmailError(HTTPException):
	"""Raised when an email error occurs."""

	def __init__(self, message: str = "Email error") -> None:
		super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


class NotFoundError(HTTPException):
	"""Raised when a requested resource does not exist."""

	def __init__(self, message: str = "Resource not found") -> None:
		super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class UnauthorizedError(HTTPException):
	"""Raised when a user is not authenticated."""

	def __init__(self, message: str = "Unauthorized") -> None:
		super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


class ForbiddenError(HTTPException):
	"""Raised when a user does not have permission to perform an action."""

	def __init__(self, message: str = "Forbidden") -> None:
		super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class ConflictError(HTTPException):
	"""Raised when a resource already exists."""

	def __init__(self, message: str = "Conflict") -> None:
		super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class InterpretationError(HTTPException):
	"""Raised when the AI interpretation service cannot produce a result."""

	def __init__(self, message: str = "AI interpretation failed") -> None:
		super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
	"""Handles all HTTPExceptions and returns a consistent error response."""
	return JSONResponse(
		status_code=exc.status_code,
		content=ErrorResponse(message=str(exc.detail)).model_dump(),
	)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
	"""Handles Pydantic validation errors and returns field-level error details."""
	errors = [
		ErrorDetail(
			field=" -> ".join(str(loc) for loc in error["loc"] if loc != "body"),
			message=error["msg"],
		)
		for error in exc.errors()
	]
	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content=ErrorResponse(message="Validation error", errors=errors).model_dump(),
	)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
	"""Catches any unhandled exceptions and returns a generic 500 response."""
	logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content=ErrorResponse(message="An unexpected error occurred. Please try again later.").model_dump(),
	)
