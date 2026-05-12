from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ocr_extract_no_file():
    response = client.post("/api/v1/ocr/extract")
    assert response.status_code == 422


def test_ocr_extract_invalid_file_type():
    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("test.pdf", b"fake content", "application/pdf")},
    )
    assert response.status_code == 415


@patch("app.services.ocr.client")
def test_ocr_extract_success(mock_openai):
    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = '{"tests": [{"name": "Haemoglobin", "value": "13.5", "unit": "g/dL", "reference_range": "12.0 - 16.0"}]}'
    mock_openai.chat.completions.create.return_value = mock_response

    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("test.jpg", b"fake image content", "image/jpeg")},
    )
    assert response.status_code == 200
    assert "tests" in response.json()
