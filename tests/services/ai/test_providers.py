import pytest

from app.core.exceptions import InterpretationError
from app.services.ai.providers import get_chat_model


class _FakeSettings:
	def __init__(self, provider: str, gemini_key: str | None = None) -> None:
		self.AI_PROVIDER = provider
		self.AI_MODEL = "gemini-1.5-flash"
		self.AI_TEMPERATURE = 0.2
		self.AI_MAX_RETRIES = 2
		self.AI_TIMEOUT_SECONDS = 30
		self.GEMINI_API_KEY = gemini_key
		self.OPENAI_API_KEY = None


def test_get_chat_model_rejects_unsupported_provider(monkeypatch):
	monkeypatch.setattr(
		"app.services.ai.providers.base.get_settings",
		lambda: _FakeSettings(provider="anthropic"),
	)
	with pytest.raises(InterpretationError):
		get_chat_model()


def test_get_chat_model_openai_placeholder_raises(monkeypatch):
	monkeypatch.setattr(
		"app.services.ai.providers.base.get_settings",
		lambda: _FakeSettings(provider="openai"),
	)
	with pytest.raises(InterpretationError):
		get_chat_model()


def test_gemini_requires_api_key(monkeypatch):
	from app.services.ai.providers import gemini

	monkeypatch.setattr(
		"app.services.ai.providers.gemini.get_settings",
		lambda: _FakeSettings(provider="gemini", gemini_key=None),
	)
	with pytest.raises(InterpretationError):
		gemini.build_gemini_chat_model()
