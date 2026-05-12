import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.core.config import get_settings


def create_access_token(
    user_id: UUID,
    *,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
    """Issue a signed JWT for `user_id`. Returns (token, ttl_seconds)."""
    settings = get_settings()
    ttl_minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    )
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    payload: dict[str, Any] = {}
    if extra_claims:
        payload.update(extra_claims)

    # Reserved claims are set unconditionally (overriding any in extra_claims)
    payload.update(
        {
            "sub": str(user_id),
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "type": "access",
        }
    )

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, ttl_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access JWT. Raises `jwt.PyJWTError` on failure.

    Requires `exp`, `sub`, and `type` claims and rejects any token whose
    `type` is not exactly `"access"` so future refresh / verification /
    password-reset tokens signed with the same secret cannot be reused here.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "type", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Token is not an access token")
    return payload
