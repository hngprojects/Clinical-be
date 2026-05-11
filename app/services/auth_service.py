from datetime import datetime, timedelta, timezone

from app.core.exceptions import UnauthorizedError
from app.core.security import (
	hash_opaque_token,
	hash_password,
	new_opaque_token,
)
from app.models.auth import PasswordResetToken
from app.models.user import User
from app.repositories.password_reset import PasswordResetRepository
from app.repositories.user import UserRepository


async def create_password_reset(
	reset_repo: PasswordResetRepository,
	user: User,
) -> str:
	"""Create a password-reset token for a user. Returns the raw (unhashed) token."""
	await reset_repo.delete_all_for_user(user.id)
	raw = new_opaque_token()
	expires = datetime.now(timezone.utc) + timedelta(minutes=60)
	password_reset_token = PasswordResetToken(
		user_id=user.id,
		token_hash=hash_opaque_token(raw),
		expires_at=expires,
		created_at=datetime.now(timezone.utc),
	)
	reset_repo.add(password_reset_token)
	await reset_repo.flush()
	return raw


async def reset_password(
	reset_repo: PasswordResetRepository,
	user_repo: UserRepository,
	raw_token: str,
	new_password: str,
) -> None:
	"""Reset a user's password using the raw reset token."""
	h = hash_opaque_token(raw_token)
	row = await reset_repo.get_by_token_hash(h, lock=True)
	now = datetime.now(timezone.utc)

	if row is None or row.expires_at < now:
		raise UnauthorizedError("Invalid or expired reset token")

	user = await user_repo.get_by_id(row.user_id)
	if not user or not user.is_active:
		raise UnauthorizedError("Invalid or expired reset token")

	user.password_hash = hash_password(new_password)
	await reset_repo.delete(row)
