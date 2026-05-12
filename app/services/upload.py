import uuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_case import MedicalCase, MedicalCaseStatus
from app.models.lab_result import LabResult, OCRStatus
from app.services.storage import upload_file

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class FileValidationError(Exception):
    """Raised when the uploaded file fails validation."""


class StorageError(Exception):
    """Raised when the storage service fails to upload the file."""


async def handle_upload(
    file: UploadFile,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    guest_session_id: str | None = None,
) -> dict:
    """
    Orchestrate the full upload flow:
    1. Validate file type and size
    2. Upload to cloud storage
    3. Create MedicalCase and LabResult records
    Returns a dict with case_id, lab_result_id, file_url, ocr_status.
    """
    # Validating the file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise FileValidationError(
            f"Unsupported file type '{file.content_type}'. "
            "Allowed types: PDF, JPG, PNG."
        )

    # Read file and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File too large. Maximum allowed size is 10MB, "
            f"got {len(content) / (1024 * 1024):.1f}MB."
        )

    # Upload to storage (failure returns 502)
    try:
        file_url = await upload_file(content, file.filename or "upload", file.content_type)
    except Exception as exc:
        raise StorageError("Failed to upload file to storage service.") from exc

    # Create MedicalCase
    medical_case = MedicalCase(
        user_id=user_id,
        guest_session_id=guest_session_id,
        status=MedicalCaseStatus.PENDING,
    )
    session.add(medical_case)
    await session.flush()

    # Create LabResult
    lab_result = LabResult(
        medical_case_id=medical_case.id,
        file={"name": file.filename or "upload", "url": file_url},
        ocr_status=OCRStatus.PENDING,
    )
    session.add(lab_result)
    await session.commit()

    return {
        "case_id": str(medical_case.id),
        "lab_result_id": str(lab_result.id),
        "file_url": file_url,
        "ocr_status": OCRStatus.PENDING.value,
    }