import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_session
from app.main import app

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def clean_overrides():
	app.dependency_overrides.clear()
	yield
	app.dependency_overrides.clear()

class MockSession:
	def __init__(self):
		pass

	def add(self, obj):
		obj.id = uuid.uuid4()
		obj.created_at = datetime.now()

	async def commit(self):
		pass

	async def refresh(self, obj):
		pass

	async def rollback(self):
		pass


async def override_get_session():
	yield MockSession()


async def test_join_waitlist(client: AsyncClient) -> None:
	app.dependency_overrides[get_session] = override_get_session

	test_email = f"test_{uuid.uuid4()}@example.com"
	with patch("app.api.v1.endpoints.waitlist.send_waitlist_email", new_callable=AsyncMock) as mock_send_email:
		response = await client.post(
			"/api/v1/waitlist/",
			json={"email": test_email},
		)
		mock_send_email.assert_called_once_with(test_email)

	assert response.status_code == 200, response.text
	json_data = response.json()
	assert json_data["status"] == "success"
	assert json_data["message"] == "Successfully joined the waitlist"
	data = json_data["data"]
	assert data["email"] == test_email
	assert "id" in data
	assert "created_at" in data


async def test_join_waitlist_duplicate(client: AsyncClient) -> None:
	test_email = f"test_{uuid.uuid4()}@example.com"

	class IntegrityMockSession(MockSession):
		def add(self, obj):
			# Original code raised IntegrityError with 3 args
			# Simulate a Postgres unique constraint error string
			raise IntegrityError("mock", "mock", Exception("duplicate key value violates unique constraint 'waitlist_email_key'"))

	async def override_get_session_fail():
		yield IntegrityMockSession()

	app.dependency_overrides[get_session] = override_get_session_fail

	response = await client.post(
		"/api/v1/waitlist/",
		json={"email": test_email},
	)
	

	assert response.status_code == 400, response.text
	
	json_resp = response.json()
	assert json_resp["message"] == "Email already in waitlist"

