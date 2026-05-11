from fastapi import APIRouter, status

from app.api.deps import WaitlistRepo
from app.core.responses import SuccessResponse
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse
from app.services.waitlist import join_waitlist

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post(
	"",
	response_model=SuccessResponse[WaitlistResponse],
	status_code=status.HTTP_201_CREATED,
)
async def join(
	payload: WaitlistCreate,
	waitlist_repo: WaitlistRepo,
) -> SuccessResponse[WaitlistResponse]:
	"""Add an email to the waitlist."""
	entry = await join_waitlist(waitlist_repo, payload)
	return SuccessResponse(
		message="You've been added to the waitlist!",
		data=WaitlistResponse.model_validate(entry),
	)
