from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DBSession
from app.models.waitlist import Waitlist
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse

router = APIRouter()

@router.post("/", response_model=WaitlistResponse)
async def join_waitlist(data: WaitlistCreate, session: DBSession) -> Waitlist:
	"""Join the waitlist."""
	try:
		waitlist_entry = Waitlist(email=data.email)
		session.add(waitlist_entry)
		await session.commit()
		await session.refresh(waitlist_entry)
		return waitlist_entry
	except IntegrityError:
		await session.rollback()
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Email already in waitlist",
		)
