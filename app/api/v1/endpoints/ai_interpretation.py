from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import AIInterpretationRepo, CurrentUser, MedicalCaseRepo
from app.core.responses import SuccessResponse
from app.schemas.ai_interpretation import AIInterpretationResponse
from app.services.ai_interpretation import (
	get_interpretation,
	get_latest_for_case,
	list_interpretations_for_case,
)

router = APIRouter(prefix="/cases/{case_id}/interpretations", tags=["ai-interpretations"])


@router.get(
	"",
	response_model=SuccessResponse[list[AIInterpretationResponse]],
)
async def list_for_case(
	case_id: UUID,
	current_user: CurrentUser,
	interp_repo: AIInterpretationRepo,
	case_repo: MedicalCaseRepo,
	offset: int = Query(0, ge=0),
	limit: int = Query(50, ge=1, le=100),
) -> SuccessResponse[list[AIInterpretationResponse]]:
	"""List AI interpretations for a medical case."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	interps = await list_interpretations_for_case(interp_repo, case_id, offset=offset, limit=limit)
	return SuccessResponse(
		message="OK",
		data=[AIInterpretationResponse.model_validate(i) for i in interps],
	)


@router.get(
	"/latest",
	response_model=SuccessResponse[AIInterpretationResponse],
)
async def latest_for_case(
	case_id: UUID,
	current_user: CurrentUser,
	interp_repo: AIInterpretationRepo,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[AIInterpretationResponse]:
	"""Get the most recent AI interpretation for a case."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	interp = await get_latest_for_case(interp_repo, case_id)
	return SuccessResponse(
		message="OK",
		data=AIInterpretationResponse.model_validate(interp),
	)


@router.get(
	"/{interpretation_id}",
	response_model=SuccessResponse[AIInterpretationResponse],
)
async def retrieve(
	case_id: UUID,
	interpretation_id: UUID,
	current_user: CurrentUser,
	interp_repo: AIInterpretationRepo,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[AIInterpretationResponse]:
	"""Retrieve a single AI interpretation."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	interp = await get_interpretation(interp_repo, interpretation_id)
	return SuccessResponse(
		message="OK",
		data=AIInterpretationResponse.model_validate(interp),
	)
