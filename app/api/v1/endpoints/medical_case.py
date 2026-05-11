from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, MedicalCaseRepo
from app.core.responses import SuccessResponse
from app.schemas.medical_case import MedicalCaseResponse
from app.services.medical_case import (
	complete_case,
	create_case_for_user,
	get_case,
	list_cases_for_user,
)

router = APIRouter(prefix="/cases", tags=["medical-cases"])


@router.post(
	"",
	response_model=SuccessResponse[MedicalCaseResponse],
	status_code=status.HTTP_201_CREATED,
)
async def create(
	current_user: CurrentUser,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[MedicalCaseResponse]:
	"""Create a new medical case for the authenticated user."""
	case = await create_case_for_user(case_repo, current_user)
	return SuccessResponse(
		message="Medical case created.",
		data=MedicalCaseResponse.model_validate(case),
	)


@router.get(
	"",
	response_model=SuccessResponse[list[MedicalCaseResponse]],
)
async def list_mine(
	current_user: CurrentUser,
	case_repo: MedicalCaseRepo,
	offset: int = Query(0, ge=0),
	limit: int = Query(50, ge=1, le=100),
) -> SuccessResponse[list[MedicalCaseResponse]]:
	"""List the authenticated user's medical cases."""
	cases, total = await list_cases_for_user(
		case_repo,
		current_user.id,
		offset=offset,
		limit=limit,
	)
	return SuccessResponse(
		message="OK",
		data=[MedicalCaseResponse.model_validate(c) for c in cases],
	)


@router.get(
	"/{case_id}",
	response_model=SuccessResponse[MedicalCaseResponse],
)
async def retrieve(
	case_id: UUID,
	current_user: CurrentUser,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[MedicalCaseResponse]:
	"""Retrieve a single medical case (ownership enforced)."""
	case = await get_case(case_repo, case_id, user=current_user)
	return SuccessResponse(
		message="OK",
		data=MedicalCaseResponse.model_validate(case),
	)


@router.post(
	"/{case_id}/complete",
	response_model=SuccessResponse[MedicalCaseResponse],
)
async def mark_complete(
	case_id: UUID,
	current_user: CurrentUser,
	case_repo: MedicalCaseRepo,
) -> SuccessResponse[MedicalCaseResponse]:
	"""Mark a medical case as complete."""
	case = await complete_case(case_repo, case_id, user=current_user)
	return SuccessResponse(
		message="Case marked as complete.",
		data=MedicalCaseResponse.model_validate(case),
	)
