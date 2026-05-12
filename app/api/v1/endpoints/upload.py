from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status, Form

from app.api.deps import OptionalCurrentUser, DBSession
from app.core.responses import SuccessResponse
from app.services.upload import FileValidationError, StorageError, handle_upload

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
)

async def upload_lab_result(
    session: DBSession,
    file: Annotated[UploadFile, File(description="Lab result file. Allowed: PDF, JPG, PNG. Max 10MB.")],
    guest_session_id: Annotated[str | None, Form()] = None,
    current_user: OptionalCurrentUser = None,
) -> SuccessResponse:
    """
    Upload a lab result file and kick off the processing pipeline.
    Accepts PDF, JPG, or PNG files up to 10MB.
    Works for both authenticated users (Bearer token) and guests (guest_session_id form field).
    On success, creates a MedicalCase and LabResult and returns their IDs.
    OCR processing begins automatically once the pipeline is wired up.
    """
    if current_user is None and not guest_session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either a valid Bearer token or a guest_session_id is required.",
        )

    try:
        result = await handle_upload(
            file=file,
            session=session,
            user_id=current_user.id if current_user else None,
            guest_session_id=guest_session_id,
        )
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SuccessResponse(
        message="File uploaded successfully.",
        data=result,
    )