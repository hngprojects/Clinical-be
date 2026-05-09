from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
from app.services.auth_service import create_password_reset, reset_password
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
	request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
) -> ForgotPasswordResponse:
	user = await session.scalar(select(User).where(User.email == request.email))
	if not user:
		raise NotFoundError("User not found")
	raw = await create_password_reset(session, user)
	await session.commit()
	send_password_reset_email(user.email, raw)
	return ForgotPasswordResponse(message=f"Password reset email sent to {user.email}")


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def password_reset(
	request: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
) -> ResetPasswordResponse:
	await reset_password(session, request.token, request.new_password)
	await session.commit()
	return ResetPasswordResponse(message="Password reset successfully")
