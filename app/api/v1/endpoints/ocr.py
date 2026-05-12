from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ocr import OCRExtractionError, extract_lab_results

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract")
async def extract_ocr(file: UploadFile = File(...)):
    SUPPORTED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Use jpeg, png, or webp.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 10MB."
        )

    try:
        result = extract_lab_results(file_bytes=file_bytes, filename=file.filename)
        return result
    except OCRExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
