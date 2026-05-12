from langchain_core.language_models import BaseChatModel

from app.core.config import get_settings
from app.core.exceptions import InterpretationError


def get_chat_model() -> BaseChatModel:
	"""Return a configured LangChain chat model for the active AI provider.

	Reads ``AI_PROVIDER`` from settings and dispatches to the matching provider
	factory. New providers are added by importing them lazily inside the branch
	so missing optional packages do not break unrelated paths.
	"""
	settings = get_settings()
	provider = (settings.AI_PROVIDER or "").lower().strip()

	if provider == "gemini":
		from app.services.ai.providers.gemini import build_gemini_chat_model

		return build_gemini_chat_model()

	if provider == "openai":
		raise InterpretationError(
			"OpenAI provider (GPT-4o-mini) is wired but not yet enabled. Set AI_PROVIDER=gemini.",
		)

	raise InterpretationError(f"Unsupported AI_PROVIDER: {provider!r}")
