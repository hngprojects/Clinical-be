from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.core.config import settings


def create_access_token(
	user_id: UUID,
	*,
	expires_minutes: int | None = None,
	extra_claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
	"""Issue a signed JWT for `user_id`. Returns (token, ttl_seconds)."""
	ttl_minutes = expires_minutes if expires_minutes is not None else settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
	now = datetime.now(timezone.utc)
	expires_at = now + timedelta(minutes=ttl_minutes)

	payload: dict[str, Any] = {
		"sub": str(user_id),
		"iat": int(now.timestamp()),
		"exp": int(expires_at.timestamp()),
		"type": "access",
	}
	if extra_claims:
		payload.update(extra_claims)

	token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
	return token, ttl_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
	"""Decode and validate a JWT. Raises `jwt.PyJWTError` on failure."""
	return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
