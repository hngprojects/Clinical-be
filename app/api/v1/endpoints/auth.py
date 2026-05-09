from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.responses import SuccessResponse
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import create_password_reset, reset_password
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth")


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
	request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
) -> SuccessResponse:
	user = await session.scalar(select(User).where(User.email == request.email))
	if not user:
		raise NotFoundError("User not found")
	raw = await create_password_reset(session, user)
	await session.commit()
	send_password_reset_email(user.email, raw)
	return SuccessResponse(message=f"Password reset email sent to {user.email}")


@router.post(
	"/reset-password",
	response_model=SuccessResponse,
)
async def password_reset(
	request: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
) -> SuccessResponse:
	await reset_password(session, request.token, request.new_password)
	await session.commit()
	return SuccessResponse(message="Password reset successfully")
