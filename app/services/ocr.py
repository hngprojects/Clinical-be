import base64
import json
import mimetypes

from openai import OpenAI


# ─── Custom Exception ────────────────────────────────────────────────────────


class OCRExtractionError(Exception):
    """Raised when OCR extraction fails for any reason."""

    pass


# ─── OpenAI Client ───────────────────────────────────────────────────────────

client = OpenAI()  # reads OPENAI_API_KEY from environment automatically


# ─── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a medical OCR assistant. Your job is to extract laboratory test results 
from images of lab reports.

Extract every test result you can find and return ONLY a valid JSON object 
with this exact structure:

{
  "tests": [
    {
      "name": "test name (e.g. Haemoglobin)",
      "value": "result value as string (e.g. 13.5)",
      "unit": "unit of measurement (e.g. g/dL)",
      "reference_range": "normal range as string (e.g. 12.0 - 16.0)"
    }
  ]
}

Rules:
- Return ONLY the JSON object, no extra text or explanation.
- If a field is not visible or not applicable, use null.
- Do not fabricate values — only extract what is clearly visible in the image.
- Include every test result on the report.
"""

USER_PROMPT = "Extract all lab test results from this lab report image."


# ─── Core Functions ──────────────────────────────────────────────────────────


def _encode_file_to_base64_url(file_bytes: bytes, filename: str) -> tuple:
    """Encode raw file bytes into a base64 Data URL."""
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "image/jpeg"

    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}", mime_type


def _validate_response(data: dict) -> dict:
    """Ensure the response contains the required structure."""
    if "tests" not in data:
        raise OCRExtractionError("AI response missing 'tests' key.")

    required_fields = {"name", "value", "unit", "reference_range"}
    for i, test in enumerate(data["tests"]):
        missing = required_fields - set(test.keys())
        if missing:
            raise OCRExtractionError(
                f"Test at index {i} is missing fields: {missing}"
            )

    return data


def extract_lab_results(file_bytes: bytes, filename: str) -> dict:
    """
    Extract structured lab test results from an image using GPT-4o-mini vision.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to detect MIME type).

    Returns:
        dict with 'tests' list, each containing name, value, unit, reference_range.

    Raises:
        OCRExtractionError: On any failure.
    """
    try:
        data_url, _ = _encode_file_to_base64_url(file_bytes, filename)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                        {
                            "type": "text",
                            "text": USER_PROMPT,
                        },
                    ],
                },
            ],
            max_tokens=2000,
        )

        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)
        validated = _validate_response(parsed)
        return validated

    except OCRExtractionError:
        raise

    except json.JSONDecodeError:
        raise OCRExtractionError("Failed to parse AI response as JSON.")

    except Exception:
        raise OCRExtractionError("OCR extraction failed. Please try again.")