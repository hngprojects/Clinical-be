from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import (
	hash_opaque_token,
	hash_password,
	new_opaque_token,
)
from app.models.auth import PasswordResetToken
from app.models.user import User


async def create_password_reset(session: AsyncSession, user: User) -> str:
	now = datetime.now(timezone.utc)
	await session.execute(
		delete(PasswordResetToken).where(
			PasswordResetToken.user_id == user.id,
			PasswordResetToken.expires_at > now,
		)
	)
	raw = new_opaque_token()
	expires = datetime.now(timezone.utc) + timedelta(minutes=60)
	password_reset_token = PasswordResetToken(
		user_id=user.id,
		token_hash=hash_opaque_token(raw),
		expires_at=expires,
		created_at=datetime.now(timezone.utc),
	)
	session.add(password_reset_token)
	await session.flush()
	return raw


async def delete_password_reset_by_raw_token(session: AsyncSession, raw_token: str) -> None:
	h = hash_opaque_token(raw_token)
	row = await session.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == h))
	if row is not None:
		await session.delete(row)
		await session.flush()


async def reset_password(session: AsyncSession, raw_token: str, new_password: str) -> None:
	h = hash_opaque_token(raw_token)
	row = await session.scalar(
		select(PasswordResetToken)
		.where(PasswordResetToken.token_hash == h)
		.with_for_update()
	)
	now = datetime.now(timezone.utc)
	if row is None or row.expires_at < now:
		raise UnauthorizedError("Invalid or expired reset token")
	user = await session.scalar(select(User).where(User.id == row.user_id))
	if not user or not user.is_active:
		raise UnauthorizedError("Invalid or expired reset token")
	user.password_hash = hash_password(new_password)
	await session.delete(row)
	await session.flush()
