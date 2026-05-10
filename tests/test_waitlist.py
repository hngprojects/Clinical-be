import uuid
from datetime import datetime

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
	response = await client.post(
		"/api/v1/waitlist/",
		json={"email": test_email},
	)
	assert response.status_code == 200, response.text
	data = response.json()
	assert data["email"] == test_email
	assert "id" in data
	assert "created_at" in data


async def test_join_waitlist_duplicate(client: AsyncClient) -> None:
	test_email = f"test_{uuid.uuid4()}@example.com"

	class IntegrityMockSession(MockSession):
		def add(self, obj):
			# Original code raised IntegrityError with 3 args
			raise IntegrityError("mock", "mock", "mock")

	async def override_get_session_fail():
		yield IntegrityMockSession()

	app.dependency_overrides[get_session] = override_get_session_fail

	response = await client.post(
		"/api/v1/waitlist/",
		json={"email": test_email},
	)
	
	if response.status_code != 400:
		print("FAILED RESPONSE JSON:", response.json())
	
	assert response.status_code == 400, response.text
	
	json_resp = response.json()
	if "detail" not in json_resp:
		print("JSON DOES NOT HAVE DETAIL:", json_resp)
		
	assert json_resp["message"] == "Email already in waitlist" if "message" in json_resp else json_resp["detail"] == "Email already in waitlist"

