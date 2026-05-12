from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.core.responses import SuccessResponse
from app.models.contact import ContactMessage
from app.schemas.contact import ContactRequest
from app.services.email import send_contact_feedback_email

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", status_code=status.HTTP_200_OK, response_model=SuccessResponse[None])
async def contact_us(payload: ContactRequest, session: DBSession) -> SuccessResponse[None]:
	record = ContactMessage(
		full_name=payload.full_name,
		email=str(payload.email),
		message=payload.message,
	)
	session.add(record)
	await session.commit()

	send_contact_feedback_email(
		full_name=payload.full_name,
		to_email=str(payload.email),
		message=payload.message,
	)
	return SuccessResponse(message="Your message has been received. We'll get back to you shortly.")
