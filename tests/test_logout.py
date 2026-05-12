"""Tests for POST /api/v1/auth/logout."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_session
from app.core.config import get_settings
from app.main import app
from app.models.user import User, UserRole
from app.services.auth.tokens import create_access_token

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_user() -> User:
	"""Build an in-memory User instance (no DB required)."""
	user = User(
		id=uuid.uuid4(),
		email="test@example.com",
		first_name="Test",
		last_name="User",
		role=UserRole.PATIENT,
		is_email_verified=True,
		is_active=True,
	)
	return user


def _make_refresh_token(user_id: uuid.UUID) -> str:
	settings = get_settings()
	now = datetime.now(timezone.utc)
	payload = {
		"sub": str(user_id),
		"jti": str(uuid.uuid4()),
		"type": "refresh",
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRES_MINUTES)).timestamp()),
	}
	return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class MockSession:
	"""Minimal async session stub used across all logout tests."""

	def add(self, obj: object) -> None:
		pass

	async def commit(self) -> None:
		pass

	async def execute(self, *args, **kwargs):  # noqa: ANN002
		# Default: return nothing (token not revoked)
		class _Result:
			rowcount = 0

			def scalar_one_or_none(self):
				return None

		return _Result()

	async def get(self, model, pk):  # noqa: ANN001
		return None


async def _override_get_session():
	yield MockSession()


# ---------------------------------------------------------------------------
# autouse fixture – wipe dependency overrides between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_overrides():
	app.dependency_overrides.clear()
	yield
	app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_logout_success(client: AsyncClient) -> None:
	"""A valid token should be accepted and revoked, returning 200."""
	user = _make_user()
	token, _ = create_access_token(user.id)
	refresh_token = _make_refresh_token(user.id)

	app.dependency_overrides[get_session] = _override_get_session
	# Bypass the real get_current_user (which needs a real DB)
	app.dependency_overrides[get_current_user] = lambda: user

	with (
		patch("app.api.v1.endpoints.auth.revoke_token", new_callable=AsyncMock) as mock_revoke,
		patch("app.api.v1.endpoints.auth.revoke_refresh_token", new_callable=AsyncMock) as mock_revoke_refresh,
	):
		response = await client.post(
			"/api/v1/auth/logout",
			headers={"Authorization": f"Bearer {token}"},
			cookies={"refresh_token": refresh_token},
		)

	assert response.status_code == 200, response.text
	body = response.json()
	assert body["status"] == "success"
	assert body["message"] == "Logged out successfully."
	mock_revoke.assert_awaited_once()
	mock_revoke_refresh.assert_awaited_once()


async def test_token_rejected_after_logout(client: AsyncClient) -> None:
	"""After logout the same token must be refused by the auth guard (401)."""
	user = _make_user()
	token, _ = create_access_token(user.id)
	refresh_token = _make_refresh_token(user.id)

	# First request: logout succeeds
	app.dependency_overrides[get_session] = _override_get_session
	app.dependency_overrides[get_current_user] = lambda: user

	with (
		patch("app.api.v1.endpoints.auth.revoke_token", new_callable=AsyncMock),
		patch("app.api.v1.endpoints.auth.revoke_refresh_token", new_callable=AsyncMock),
	):
		logout_resp = await client.post(
			"/api/v1/auth/logout",
			headers={"Authorization": f"Bearer {token}"},
			cookies={"refresh_token": refresh_token},
		)
	assert logout_resp.status_code == 200

	# Second request: is_token_revoked now returns True
	class RevokedSession(MockSession):
		async def execute(self, *args, **kwargs):
			class _Result:
				def scalar_one_or_none(self):
					return uuid.uuid4()  # non-None → revoked

			return _Result()

	async def _revoked_session():
		yield RevokedSession()

	# Remove the get_current_user override so the real guard runs
	app.dependency_overrides.pop(get_current_user, None)
	app.dependency_overrides[get_session] = _revoked_session

	me_resp = await client.get(
		"/api/v1/auth/me",
		headers={"Authorization": f"Bearer {token}"},
	)
	assert me_resp.status_code == 401
	assert "revoked" in me_resp.json()["message"].lower()


async def test_logout_requires_auth(client: AsyncClient) -> None:
	"""A request with no Authorization header must return 401."""
	response = await client.post("/api/v1/auth/logout")
	assert response.status_code == 401


async def test_logout_with_already_revoked_token(client: AsyncClient) -> None:
	"""The auth guard rejects a blocklisted token before reaching the handler."""
	user = _make_user()
	token, _ = create_access_token(user.id)

	class RevokedSession(MockSession):
		async def execute(self, *args, **kwargs):
			class _Result:
				def scalar_one_or_none(self):
					return uuid.uuid4()

			return _Result()

		async def get(self, model, pk):
			return user

	async def _revoked_session():
		yield RevokedSession()

	app.dependency_overrides[get_session] = _revoked_session

	response = await client.post(
		"/api/v1/auth/logout",
		headers={"Authorization": f"Bearer {token}"},
	)
	assert response.status_code == 401
	assert "revoked" in response.json()["message"].lower()
