from app.core.exceptions import ConflictError
from app.models.waitlist import Waitlist
from app.repositories.waitlist import WaitlistRepository
from app.schemas.waitlist import WaitlistCreate


async def join_waitlist(
	waitlist_repo: WaitlistRepository,
	payload: WaitlistCreate,
) -> Waitlist:
	"""Add an email to the waitlist. Raises ConflictError if already present."""
	email = payload.email.strip().lower()
	existing = await waitlist_repo.get_by_email(email)
	if existing is not None:
		raise ConflictError("This email is already on the waitlist.")
	entry = Waitlist(email=email)
	waitlist_repo.add(entry)
	await waitlist_repo.commit()
	await waitlist_repo.refresh(entry)
	return entry
