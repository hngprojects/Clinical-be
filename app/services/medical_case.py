from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.medical_case import MedicalCase, MedicalCaseStatus
from app.models.user import User
from app.repositories.medical_case import MedicalCaseRepository
from app.schemas.medical_case import MedicalCaseCreate, MedicalCaseUpdate


async def create_case(
	case_repo: MedicalCaseRepository,
	payload: MedicalCaseCreate,
) -> MedicalCase:
	"""Create a new medical case."""
	case = MedicalCase(
		user_id=payload.user_id,
		guest_session_id=payload.guest_session_id,
		status=payload.status,
	)
	case_repo.add(case)
	await case_repo.commit()
	await case_repo.refresh(case)
	return case


async def create_case_for_user(
	case_repo: MedicalCaseRepository,
	user: User,
) -> MedicalCase:
	"""Shorthand: create a PENDING case for an authenticated user."""
	case = MedicalCase(
		user_id=user.id,
		status=MedicalCaseStatus.PENDING,
	)
	case_repo.add(case)
	await case_repo.commit()
	await case_repo.refresh(case)
	return case


async def get_case(
	case_repo: MedicalCaseRepository,
	case_id: UUID,
	*,
	user: User | None = None,
) -> MedicalCase:
	"""Fetch a single case. If *user* is provided, enforces ownership."""
	case = await case_repo.get_by_id(case_id)
	if case is None:
		raise NotFoundError("Medical case not found.")
	if user is not None and case.user_id != user.id:
		raise ForbiddenError("You do not have access to this case.")
	return case


async def list_cases_for_user(
	case_repo: MedicalCaseRepository,
	user_id: UUID,
	*,
	offset: int = 0,
	limit: int = 50,
) -> tuple[list[MedicalCase], int]:
	"""Return paginated cases for a user together with the total count."""
	cases = await case_repo.list_by_user(user_id, offset=offset, limit=limit)
	total = await case_repo.count_by_user(user_id)
	return cases, total


async def update_case(
	case_repo: MedicalCaseRepository,
	case_id: UUID,
	payload: MedicalCaseUpdate,
	*,
	user: User | None = None,
) -> MedicalCase:
	"""Partially update a medical case."""
	case = await get_case(case_repo, case_id, user=user)
	if payload.status is not None:
		case.status = payload.status
	if payload.completed_at is not None:
		case.completed_at = payload.completed_at
	await case_repo.commit()
	await case_repo.refresh(case)
	return case


async def complete_case(
	case_repo: MedicalCaseRepository,
	case_id: UUID,
	*,
	user: User | None = None,
) -> MedicalCase:
	"""Mark a case as complete."""
	case = await get_case(case_repo, case_id, user=user)
	case.status = MedicalCaseStatus.COMPLETE
	case.completed_at = datetime.now(timezone.utc)
	await case_repo.commit()
	await case_repo.refresh(case)
	return case
