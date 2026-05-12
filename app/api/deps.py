from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.db.session import get_session
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.services.auth.blocklist import is_token_revoked
from app.services.auth.tokens import decode_access_token

DBSession = Annotated[AsyncSession, Depends(get_session)]

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
	session: DBSession,
	credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
	"""Resolve the authenticated user from a Bearer JWT."""
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise UnauthorizedError("Missing or invalid Authorization header.")

	try:
		payload = decode_access_token(credentials.credentials)
	except jwt.ExpiredSignatureError as exc:
		raise UnauthorizedError("Token has expired.") from exc
	except jwt.PyJWTError as exc:
		raise UnauthorizedError("Invalid authentication token.") from exc

	# Check if this token has been explicitly revoked via logout
	jti = payload.get("jti")
	if jti:
		blacklisted = await session.get(TokenBlacklist, jti)
		if blacklisted is not None:
			raise UnauthorizedError("Token has been revoked. Please log in again.")

	subject = payload.get("sub")
	if not subject:
		raise UnauthorizedError("Invalid authentication token.")

	try:
		user_id = UUID(str(subject))
	except ValueError as exc:
		raise UnauthorizedError("Invalid authentication token.") from exc

	user = await session.get(User, user_id)
	if user is None or not user.is_active:
		raise UnauthorizedError("User not found or disabled.")
	if not user.is_email_verified:
		raise UnauthorizedError("Email address not verified.")
	return user


CurrentUser = Annotated[User, Depends(get_current_user)]
