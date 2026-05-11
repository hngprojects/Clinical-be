from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, LabResultRepo, MedicalCaseRepo
from app.core.responses import SuccessResponse
from app.schemas.lab_result import LabResultCreate, LabResultResponse
from app.services.lab_result import (
	create_lab_result,
	get_lab_result,
	list_lab_results_for_case,
)

router = APIRouter(prefix="/cases/{case_id}/lab-results", tags=["lab-results"])


@router.post(
	"",
	response_model=SuccessResponse[LabResultResponse],
	status_code=status.HTTP_201_CREATED,
)
async def create(
	case_id: UUID,
	payload: LabResultCreate,
	current_user: CurrentUser,
	lab_repo: LabResultRepo,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[LabResultResponse]:
	"""Upload a new lab result to a medical case."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	payload.medical_case_id = case_id
	result = await create_lab_result(lab_repo, case_repo, payload)
	return SuccessResponse(
		message="Lab result created.",
		data=LabResultResponse.model_validate(result),
	)


@router.get(
	"",
	response_model=SuccessResponse[list[LabResultResponse]],
)
async def list_for_case(
	case_id: UUID,
	current_user: CurrentUser,
	lab_repo: LabResultRepo,
	case_repo: MedicalCaseRepo,
	offset: int = Query(0, ge=0),
	limit: int = Query(50, ge=1, le=100),
) -> SuccessResponse[list[LabResultResponse]]:
	"""List lab results for a medical case."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	results = await list_lab_results_for_case(lab_repo, case_id, offset=offset, limit=limit)
	return SuccessResponse(
		message="OK",
		data=[LabResultResponse.model_validate(r) for r in results],
	)


@router.get(
	"/{result_id}",
	response_model=SuccessResponse[LabResultResponse],
)
async def retrieve(
	case_id: UUID,
	result_id: UUID,
	current_user: CurrentUser,
	lab_repo: LabResultRepo,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[LabResultResponse]:
	"""Retrieve a single lab result."""
	from app.services.medical_case import get_case

	await get_case(case_repo, case_id, user=current_user)
	result = await get_lab_result(lab_repo, result_id)
	return SuccessResponse(
		message="OK",
		data=LabResultResponse.model_validate(result),
	)
