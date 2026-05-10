from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse
from app.services.waitlist import create_waitlist_entry

#Router configuration
router = APIRouter()

# Waitlist Registration Endpoint
@router.post(
    "/join",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join the waitlist",
    description="Submit an email address to join the clinical app waitlist.",
)
async def join_waitlist(
    payload: WaitlistCreate,
    db: DBSession,
):
    entry = await create_waitlist_entry(db=db, payload=payload)
    return entry