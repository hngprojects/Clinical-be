from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.ai_interpretation import AIInterpretation, InterpretationStatus
from app.repositories.ai_interpretation import AIInterpretationRepository
from app.repositories.medical_case import MedicalCaseRepository
from app.schemas.ai_interpretation import AIInterpretationCreate, AIInterpretationUpdate


async def create_interpretation(
	interp_repo: AIInterpretationRepository,
	case_repo: MedicalCaseRepository,
	payload: AIInterpretationCreate,
) -> AIInterpretation:
	"""Create a new AI interpretation record for a medical case."""
	case = await case_repo.get_by_id(payload.medical_case_id)
	if case is None:
		raise NotFoundError("Medical case not found.")

	interp = AIInterpretation(
		medical_case_id=payload.medical_case_id,
		summary=payload.summary,
		value_breakdown=[v.model_dump() for v in payload.value_breakdown] if payload.value_breakdown else None,
		suggested_questions=payload.suggested_questions,
		risk_level=payload.risk_level,
		confidence=payload.confidence,
		status=InterpretationStatus.PENDING,
	)
	interp_repo.add(interp)
	await interp_repo.commit()
	await interp_repo.refresh(interp)
	return interp


async def get_interpretation(
	interp_repo: AIInterpretationRepository,
	interp_id: UUID,
) -> AIInterpretation:
	interp = await interp_repo.get_by_id(interp_id)
	if interp is None:
		raise NotFoundError("AI interpretation not found.")
	return interp


async def get_latest_for_case(
	interp_repo: AIInterpretationRepository,
	medical_case_id: UUID,
) -> AIInterpretation:
	interp = await interp_repo.get_latest_for_case(medical_case_id)
	if interp is None:
		raise NotFoundError("No interpretation found for this case.")
	return interp


async def list_interpretations_for_case(
	interp_repo: AIInterpretationRepository,
	medical_case_id: UUID,
	*,
	offset: int = 0,
	limit: int = 50,
) -> list[AIInterpretation]:
	return await interp_repo.list_by_case(medical_case_id, offset=offset, limit=limit)


async def update_interpretation(
	interp_repo: AIInterpretationRepository,
	interp_id: UUID,
	payload: AIInterpretationUpdate,
) -> AIInterpretation:
	"""Partially update an AI interpretation."""
	interp = await get_interpretation(interp_repo, interp_id)
	for field in ("summary", "value_breakdown", "suggested_questions", "risk_level", "confidence", "status"):
		value = getattr(payload, field, None)
		if value is not None:
			if field == "value_breakdown":
				value = [v.model_dump() for v in value]
			setattr(interp, field, value)
	await interp_repo.commit()
	await interp_repo.refresh(interp)
	return interp
