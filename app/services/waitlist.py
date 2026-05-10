import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.waitlist import Waitlist
from app.schemas.waitlist import WaitlistCreate
from app.services.email import send_waitlist_welcome

logger = logging.getLogger(__name__)


async def create_waitlist_entry(db: AsyncSession, payload: WaitlistCreate) -> Waitlist:
    """
    Add an email to the waitlist.
    Raises ConflictError (409) if duplicate.
    Saves to DB first, then sends welcome email silently.
    """
    # Check for duplicate
    result = await db.execute(
        select(Waitlist).where(Waitlist.email == payload.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise ConflictError("This email is already on the waitlist.")

    # Create the entry — id and created_at are auto-set by the model
    entry = Waitlist(email=payload.email)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    # Send welcome email — failure is caught and logged, never breaks the signup
    try:
        await send_waitlist_welcome(email=payload.email)
    except Exception as exc:
        logger.error("Failed to send waitlist welcome email to %s: %s", payload.email, exc)

    return entry