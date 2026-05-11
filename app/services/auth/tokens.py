import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_opaque_token
from app.models.auth import RefreshToken
from app.models.user import User
from app.services.auth.blocklist import revoke_token


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


async def create_refresh_token(user_id: UUID, session: AsyncSession) -> str:
	"""Persist a new refresh JWT and store its SHA-256 hash for `user_id`.

	Returns the raw JWT string for the client.
	"""
	now = datetime.now(timezone.utc)
	settings = get_settings()
	payload = {
		"sub": str(user_id),
		"jti": str(uuid.uuid4()),
		"type": "refresh",
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES)).timestamp()),
	}
	token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
	refresh_token = RefreshToken(
		user_id=user_id,
		token_hash=hash_opaque_token(token),
		expires_at=now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES),
	)
	session.add(refresh_token)
	await session.commit()
	return token


def decode_refresh_token(token: str) -> dict[str, Any]:
	"""Decode a refresh JWT. Raises `jwt.InvalidTokenError` when `type` is not `refresh`."""
	settings = get_settings()
	payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
	if payload.get("type") != "refresh":
		raise jwt.InvalidTokenError("Token is not a refresh token")
	return payload


async def revoke_refresh_token(token: str, session: AsyncSession) -> RefreshToken:
	"""Mark the refresh row matching ``token``'s hash as revoked (idempotent-ish).

	Revokes the refresh token by adding to blocklist and deleting the row from the database.
	Raises ``UnauthorizedError`` if no eligible row existed (unknown or already revoked token).
	"""
	payload = decode_refresh_token(token)
	jti: str = payload["jti"]
	user_id = payload.get("sub")
	expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
	await revoke_token(session, jti=jti, user_id=UUID(user_id), expires_at=expires_at)
	h = hash_opaque_token(token)
	result = await session.execute(delete(RefreshToken).where(RefreshToken.token_hash == h))
	if result.rowcount == 0:
		raise UnauthorizedError(message="Refresh token not found or already revoked")
	await session.commit()


async def rotate_all_tokens(*, session: AsyncSession, refresh_token: str) -> dict:
	"""Rotate the refresh token for a user.
	On success returns keys `access_token`, `refresh_token`, and `expires_in` (TTL seconds).
	"""
	payload = decode_refresh_token(refresh_token)
	user_id = payload.get("sub")
	if not user_id:
		raise UnauthorizedError(message="Invalid refresh token")
	user = await session.get(User, UUID(user_id))
	if not user:
		raise UnauthorizedError(message="User not found")
	token, ttl_seconds = create_access_token(user.id)
	new_refresh = await create_refresh_token(user.id, session)
	return {"access_token": token, "refresh_token": new_refresh, "expires_in": ttl_seconds}
