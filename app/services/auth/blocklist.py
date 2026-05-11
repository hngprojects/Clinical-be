from datetime import datetime
from uuid import UUID

from app.repositories.token_blocklist import TokenBlocklistRepository


async def revoke_token(
	blocklist_repo: TokenBlocklistRepository,
	*,
	jti: str,
	user_id: UUID,
	expires_at: datetime,
) -> None:
	"""Insert a revoked token record and commit the transaction."""
	await blocklist_repo.revoke(jti=jti, user_id=user_id, expires_at=expires_at)


async def is_token_revoked(blocklist_repo: TokenBlocklistRepository, jti: str) -> bool:
	"""Return ``True`` if *jti* has been explicitly revoked."""
	return await blocklist_repo.is_revoked(jti)
