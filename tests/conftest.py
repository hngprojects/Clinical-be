import os
import pytest


# ---------------------------------------------------------------------------
# CLI option — lets you run against a live server:
#   pytest tests/smoke_test.py -v --base-url=http://localhost:8000
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
	parser.addoption(
		"--base-url",
		action="store",
		default=None,
		help="Base URL of a running server. If set, smoke tests hit the live server.",
	)


def pytest_configure(config):
	base = config.getoption("--base-url", default=None)
	if base:
		os.environ["TEST_BASE_URL"] = base


# ---------------------------------------------------------------------------
# ASGI fixture — only imported when test_health.py actually requests it.
# Lazy import prevents ModuleNotFoundError when running smoke_test.py
# without the full app dependencies installed.
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
	os.environ.setdefault(
		"DATABASE_URL",
		"postgresql+asyncpg://postgres:postgres@localhost:5432/test",
	)
	from httpx import ASGITransport, AsyncClient
	from app.main import app

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		yield ac