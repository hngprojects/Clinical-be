from sqlalchemy import select

from app.models.waitlist import Waitlist
from app.repositories.base import BaseRepository


class WaitlistRepository(BaseRepository[Waitlist]):
	model = Waitlist

	async def get_by_email(self, email: str) -> Waitlist | None:
		normalized = email.strip().lower()
		result = await self._session.execute(select(Waitlist).where(Waitlist.email == normalized))
		return result.scalar_one_or_none()
