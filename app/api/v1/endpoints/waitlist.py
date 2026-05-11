from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DBSession
from app.core.responses import SuccessResponse
from app.models.waitlist import Waitlist
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse
from app.services.email import send_waitlist_email

router = APIRouter()


@router.post("/", response_model=SuccessResponse[WaitlistResponse])
async def join_waitlist(
	data: WaitlistCreate, session: DBSession, background_tasks: BackgroundTasks
) -> SuccessResponse[WaitlistResponse]:
	"""Join the waitlist."""
	try:
		waitlist_entry = Waitlist(email=data.email)
		session.add(waitlist_entry)
		await session.commit()
		await session.refresh(waitlist_entry)

		# Send the waitlist welcome email in the background
		background_tasks.add_task(send_waitlist_email, waitlist_entry.email)

		return SuccessResponse(
			message="Successfully joined the waitlist",
			data=WaitlistResponse.model_validate(waitlist_entry),
		)
	except IntegrityError as e:
		await session.rollback()
		# Check if the error is specifically about email uniqueness
		error_info = str(e.orig) if hasattr(e, "orig") else str(e)
		if "email" in error_info.lower() or "unique" in error_info.lower():
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Email already in waitlist",
			)
		# Re-raise for unexpected integrity errors
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Database integrity error",
		)
