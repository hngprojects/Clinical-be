from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.responses import SuccessResponse

router = APIRouter()

# Directory where uploaded files will be stored temporarily
UPLOAD_DIR = Path("uploads")

# Maximum allowed upload size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported file MIME types
ALLOWED_CONTENT_TYPES = {
	"application/pdf",
	"image/png",
	"image/jpeg",
}


@router.post(
	"/upload",
	response_model=SuccessResponse[dict],
	status_code=status.HTTP_201_CREATED,
)
async def upload_file(
	file: UploadFile = File(...),
) -> SuccessResponse[dict]:
	"""
	Upload a document file for downstream OCR and AI processing.
	"""

	# Validate uploaded file type
	if file.content_type not in ALLOWED_CONTENT_TYPES:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Unsupported file type. Only PDF, PNG, and JPEG files are allowed.",
		)

	# Read uploaded file into memory
	file_bytes = await file.read()

	# Validate maximum file size
	if len(file_bytes) > MAX_FILE_SIZE:
		raise HTTPException(
			status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
			detail="File size exceeds the 10MB limit.",
		)

	# Create upload directory if it does not exist
	UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

	original_filename = file.filename or "uploaded_file"

	# Preserve original file extension
	file_extension = Path(original_filename).suffix

	# Generate unique filename to avoid collisions
	stored_filename = f"{uuid4()}{file_extension}"

	file_path = UPLOAD_DIR / stored_filename

	# Save uploaded file locally
	file_path.write_bytes(file_bytes)

	return SuccessResponse(
		message="File uploaded successfully.",
		data={
			"original_filename": original_filename,
			"stored_filename": stored_filename,
			"content_type": file.content_type,
			"size_bytes": len(file_bytes),
			"file_path": str(file_path),
		},
	)
