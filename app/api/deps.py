from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.db.session import get_session
from app.models.user import User
from app.repositories.ai_interpretation import AIInterpretationRepository
from app.repositories.chat import ChatRepository
from app.repositories.lab_result import LabResultRepository
from app.repositories.medical_case import MedicalCaseRepository
from app.repositories.notification import NotificationRepository
from app.repositories.otp import OtpRepository
from app.repositories.password_reset import PasswordResetRepository
from app.repositories.token_blocklist import TokenBlocklistRepository
from app.repositories.user import UserRepository
from app.repositories.waitlist import WaitlistRepository
from app.services.auth.tokens import decode_access_token

DBSession = Annotated[AsyncSession, Depends(get_session)]

bearer_scheme = HTTPBearer(auto_error=False)


# Repository dependencies
def get_user_repo(session: DBSession) -> UserRepository:
	return UserRepository(session)


def get_otp_repo(session: DBSession) -> OtpRepository:
	return OtpRepository(session)


def get_token_blocklist_repo(session: DBSession) -> TokenBlocklistRepository:
	return TokenBlocklistRepository(session)


def get_password_reset_repo(session: DBSession) -> PasswordResetRepository:
	return PasswordResetRepository(session)


def get_medical_case_repo(session: DBSession) -> MedicalCaseRepository:
	return MedicalCaseRepository(session)


def get_lab_result_repo(session: DBSession) -> LabResultRepository:
	return LabResultRepository(session)


def get_ai_interpretation_repo(session: DBSession) -> AIInterpretationRepository:
	return AIInterpretationRepository(session)


def get_chat_repo(session: DBSession) -> ChatRepository:
	return ChatRepository(session)


def get_notification_repo(session: DBSession) -> NotificationRepository:
	return NotificationRepository(session)


def get_waitlist_repo(session: DBSession) -> WaitlistRepository:
	return WaitlistRepository(session)


# Annotated shortcuts
UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
OtpRepo = Annotated[OtpRepository, Depends(get_otp_repo)]
TokenBlocklistRepo = Annotated[TokenBlocklistRepository, Depends(get_token_blocklist_repo)]
PasswordResetRepo = Annotated[PasswordResetRepository, Depends(get_password_reset_repo)]
MedicalCaseRepo = Annotated[MedicalCaseRepository, Depends(get_medical_case_repo)]
LabResultRepo = Annotated[LabResultRepository, Depends(get_lab_result_repo)]
AIInterpretationRepo = Annotated[AIInterpretationRepository, Depends(get_ai_interpretation_repo)]
ChatRepo = Annotated[ChatRepository, Depends(get_chat_repo)]
NotificationRepo = Annotated[NotificationRepository, Depends(get_notification_repo)]
WaitlistRepo = Annotated[WaitlistRepository, Depends(get_waitlist_repo)]


# Auth guard


async def get_current_user(
	user_repo: UserRepo,
	blocklist_repo: TokenBlocklistRepo,
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

	jti = payload.get("jti")
	if not jti or await blocklist_repo.is_revoked(jti):
		raise UnauthorizedError("Token has been revoked.")

	subject = payload.get("sub")
	if not subject:
		raise UnauthorizedError("Invalid authentication token.")

	try:
		user_id = UUID(str(subject))
	except ValueError as exc:
		raise UnauthorizedError("Invalid authentication token.") from exc

	user = await user_repo.get_by_id(user_id)
	if user is None or not user.is_active:
		raise UnauthorizedError("User not found or disabled.")
	if not user.is_email_verified:
		raise UnauthorizedError("Email address not verified.")
	return user


CurrentUser = Annotated[User, Depends(get_current_user)]
