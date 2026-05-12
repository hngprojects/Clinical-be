from langchain_core.language_models import BaseChatModel

from app.core.config import get_settings
from app.core.exceptions import InterpretationError


def build_gemini_chat_model() -> BaseChatModel:
	"""Build a Gemini-backed LangChain chat model from settings."""
	settings = get_settings()
	if not settings.GEMINI_API_KEY:
		raise InterpretationError("GEMINI_API_KEY is not configured.")

	try:
		from langchain_google_genai import ChatGoogleGenerativeAI
	except ImportError as exc:
		raise InterpretationError(
			"langchain-google-genai is not installed. Run `uv sync` to install AI dependencies.",
		) from exc

	return ChatGoogleGenerativeAI(
		model=settings.AI_MODEL,
		google_api_key=settings.GEMINI_API_KEY,
		temperature=settings.AI_TEMPERATURE,
		timeout=settings.AI_TIMEOUT_SECONDS,
		max_retries=settings.AI_MAX_RETRIES,
	)
