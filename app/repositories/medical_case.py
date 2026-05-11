from uuid import UUID

from sqlalchemy import func, select

from app.models.medical_case import MedicalCase, MedicalCaseStatus
from app.repositories.base import BaseRepository


class MedicalCaseRepository(BaseRepository[MedicalCase]):
	model = MedicalCase

	async def list_by_user(
		self,
		user_id: UUID,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[MedicalCase]:
		result = await self._session.execute(
			select(MedicalCase)
			.where(MedicalCase.user_id == user_id)
			.order_by(MedicalCase.created_at.desc())
			.offset(offset)
			.limit(limit)
		)
		return list(result.scalars().all())

	async def count_by_user(self, user_id: UUID) -> int:
		result = await self._session.execute(
			select(func.count()).select_from(MedicalCase).where(MedicalCase.user_id == user_id)
		)
		return result.scalar_one()

	async def get_by_guest_session(
		self,
		guest_session_id: str,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[MedicalCase]:
		result = await self._session.execute(
			select(MedicalCase)
			.where(MedicalCase.guest_session_id == guest_session_id)
			.order_by(MedicalCase.created_at.desc())
			.offset(offset)
			.limit(limit)
		)
		return list(result.scalars().all())

	async def update_status(self, case_id: UUID, status: MedicalCaseStatus) -> MedicalCase | None:
		case = await self.get_by_id(case_id)
		if case is None:
			return None
		case.status = status
		return case
