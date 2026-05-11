from uuid import UUID

from sqlalchemy import select

from app.models.ai_interpretation import AIInterpretation, InterpretationStatus
from app.repositories.base import BaseRepository


class AIInterpretationRepository(BaseRepository[AIInterpretation]):
	model = AIInterpretation

	async def list_by_case(
		self,
		medical_case_id: UUID,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[AIInterpretation]:
		result = await self._session.execute(
			select(AIInterpretation)
			.where(AIInterpretation.medical_case_id == medical_case_id)
			.order_by(AIInterpretation.generated_at.desc())
			.offset(offset)
			.limit(limit)
		)
		return list(result.scalars().all())

	async def get_latest_for_case(self, medical_case_id: UUID) -> AIInterpretation | None:
		result = await self._session.execute(
			select(AIInterpretation)
			.where(AIInterpretation.medical_case_id == medical_case_id)
			.order_by(AIInterpretation.generated_at.desc())
			.limit(1)
		)
		return result.scalar_one_or_none()

	async def update_status(
		self,
		interp_id: UUID,
		status: InterpretationStatus,
	) -> AIInterpretation | None:
		interp = await self.get_by_id(interp_id)
		if interp is None:
			return None
		interp.status = status
		return interp
