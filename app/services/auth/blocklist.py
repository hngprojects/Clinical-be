from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blocklist import TokenBlocklist


async def revoke_token(
	session: AsyncSession,
	*,
	jti: str,
	user_id: UUID,
	expires_at: datetime,
) -> None:
	"""Insert a revoked token record and commit the transaction.

	Args:
		session:    The active async DB session.
		jti:        The JWT ID claim extracted from the access token.
		user_id:    The ID of the user who owns the token.
		expires_at: The token's original expiry (from the `exp` claim).
	"""
	entry = TokenBlocklist(jti=jti, user_id=user_id, expires_at=expires_at)
	session.add(entry)
	await session.commit()


async def is_token_revoked(session: AsyncSession, jti: str) -> bool:
	"""Return ``True`` if *jti* has been explicitly revoked.

	Uses a lightweight ``EXISTS``-style scalar query to avoid fetching the
	full row.
	"""
	result = await session.execute(
		select(TokenBlocklist.id).where(TokenBlocklist.jti == jti).limit(1)
	)
	return result.scalar_one_or_none() is not None
