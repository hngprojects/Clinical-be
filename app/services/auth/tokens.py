from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_opaque_token
from app.models.auth import RefreshToken
from app.models.user import User


def create_access_token(
	user_id: UUID,
	*,
	expires_minutes: int | None = None,
	extra_claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
	"""Issue a signed JWT for `user_id`. Returns (token, ttl_seconds)."""
	settings = get_settings()
	ttl_minutes = expires_minutes if expires_minutes is not None else settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
	now = datetime.now(timezone.utc)
	expires_at = now + timedelta(minutes=ttl_minutes)

	payload: dict[str, Any] = {}
	if extra_claims:
		payload.update(extra_claims)

	# Reserved claims are set unconditionally (overriding any in extra_claims)
	payload.update(
		{
			"sub": str(user_id),
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
		options={"require": ["exp", "sub", "type"]},
	)
	if payload.get("type") != "access":
		raise jwt.InvalidTokenError("Token is not an access token")
	return payload


def create_refresh_token(user_id: UUID, session: Session) -> str:
	now = datetime.now(timezone.utc)
	settings = get_settings()
	payload = {
		"sub": str(user_id),
		"type": "refresh",
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES)).timestamp()),
	}
	token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
	refresh_token = RefreshToken(
		token_hash=hash_opaque_token(token),
		expires_at=now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES),
	)
	session.add(refresh_token)
	session.commit()
	session.refresh(refresh_token)
	return token


def decode_refresh_token(token: str) -> dict[str, Any]:
	settings = get_settings()
	payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
	if payload.get("type") != "refresh":
		raise jwt.InvalidTokenError("Token is not a refresh token")
	return payload


async def revoke_refresh_token(token: str, session: Session):
	refresh_token = await session.get(RefreshToken, hash_opaque_token(token))
	if not refresh_token:
		raise UnauthorizedError(message="Refresh token not found")
	if refresh_token.is_revoked:
		raise UnauthorizedError(message="Refresh token has been revoked")
	refresh_token.is_revoked = True
	session.commit()
	session.refresh(refresh_token)
	return refresh_token


async def refresh_all_tokens(*, session: Session, refresh_token: str) -> dict:
	payload = decode_refresh_token(refresh_token)
	user_id = payload.get("sub")
	if not user_id:
		raise UnauthorizedError(message="Invalid refresh token")
	user = await session.get(User, UUID(user_id))
	if not user:
		raise UnauthorizedError(message="User not found")
	revoke_refresh_token(refresh_token, session)
	access_token, _ = create_access_token(user.id)
	refresh_token = create_refresh_token(user.id, session)

	return {"access_token": access_token, "refresh_token": refresh_token}
