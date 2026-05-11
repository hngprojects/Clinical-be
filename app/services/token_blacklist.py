from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blacklist import TokenBlacklist


async def purge_expired_tokens(session: AsyncSession) -> int:
	"""
	Delete blacklist entries whose tokens have already expired naturally.

	These rows are safe to remove because an expired token would be
	rejected by JWT signature validation before the blacklist is even checked.
	Should be run periodically (e.g. daily) to keep the table small.

	Returns the number of rows deleted.
	"""
	now = datetime.now(timezone.utc)
	result = await session.execute(
		delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
	)
	await session.commit()
	return result.rowcount