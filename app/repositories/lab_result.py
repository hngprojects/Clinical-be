from uuid import UUID

from sqlalchemy import select

from app.models.lab_result import LabResult, OCRStatus
from app.repositories.base import BaseRepository


class LabResultRepository(BaseRepository[LabResult]):
	model = LabResult

	async def list_by_case(
		self,
		medical_case_id: UUID,
		*,
		offset: int = 0,
		limit: int = 50,
	) -> list[LabResult]:
		result = await self._session.execute(
			select(LabResult)
			.where(LabResult.medical_case_id == medical_case_id)
			.order_by(LabResult.created_at.desc())
			.offset(offset)
			.limit(limit)
		)
		return list(result.scalars().all())

	async def update_ocr_status(self, result_id: UUID, status: OCRStatus) -> LabResult | None:
		lab_result = await self.get_by_id(result_id)
		if lab_result is None:
			return None
		lab_result.ocr_status = status
		return lab_result
