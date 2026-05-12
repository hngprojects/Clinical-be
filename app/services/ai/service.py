import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict

from app.core.exceptions import InterpretationError
from app.models.ai_interpretation import Confidence, RiskLevel
from app.schemas.ai_interpretation import ValueBreakdown
from app.services.ai.graph import build_graph
from app.services.ai.llm_schemas import LLMValueBreakdown
from app.services.ai.providers import get_chat_model

logger = logging.getLogger(__name__)


class InterpretationResult(BaseModel):
	"""Pure-data result returned by :func:`interpret`.

	This intentionally mirrors the LLM-derived subset of ``AIInterpretationBase``
	but with non-optional fields, so callers know every field is populated on a
	successful call. Persistence (writing to ``ai_interpretation`` rows) is the
	caller's responsibility — either a FastAPI endpoint or a future Celery worker.
	"""

	summary: str
	value_breakdown: list[ValueBreakdown]
	suggested_questions: list[str]
	risk_level: RiskLevel
	confidence: Confidence

	model_config = ConfigDict(frozen=True)


def _to_value_breakdown(items: list[LLMValueBreakdown]) -> list[ValueBreakdown]:
	"""Convert LLM breakdown items to the public ``ValueBreakdown`` schema."""
	return [ValueBreakdown(metric=item.metric, value=item.value, unit=item.unit, status=item.status) for item in items]


def interpret(
	extracted_values: dict[str, Any],
	*,
	chat_model: BaseChatModel | None = None,
) -> InterpretationResult:
	"""Generate a structured AI interpretation for a set of extracted lab values.

	Args:
		extracted_values: The ``extracted_values`` payload from a ``LabResult`` row.
			Must be a non-empty mapping. Shape is intentionally open — the LLM is
			responsible for normalising metric names, units, and reference ranges.
		chat_model: Optional pre-built LangChain chat model. When omitted, the
			provider configured by ``AI_PROVIDER`` is used. Injection here exists
			primarily so tests can pass a fake model without monkey-patching.

	Returns:
		An immutable :class:`InterpretationResult` containing the disclaimer-prefixed
		summary, per-value breakdown, suggested questions, a deterministically
		derived ``risk_level``, and the LLM's self-reported ``confidence``.

	Raises:
		InterpretationError: For any failure — bad input, provider failure, schema
			mismatch, or an unconfigured provider. The function is intentionally
			**pure**: it does not read or write the database. Persisting the result
			is the caller's responsibility, which keeps this safe to invoke from a
			FastAPI endpoint today and from a Celery worker later without changes.

	Note:
		This function is sync-callable. The LangGraph + LangChain stack is itself
		async-aware, but exposing a synchronous surface keeps the API trivial to
		hand off to Celery (``celery_task.delay(values)``) when we move heavy
		interpretation off the request thread.
	"""
	model = chat_model if chat_model is not None else get_chat_model()

	graph = build_graph()

	try:
		final_state = graph.invoke(
			{"extracted_values": extracted_values, "chat_model": model},
		)
	except InterpretationError:
		raise
	except Exception as exc:  # noqa: BLE001 - normalize any unexpected graph failure
		logger.exception("AI interpretation graph failed unexpectedly")
		raise InterpretationError("AI interpretation pipeline failed.") from exc

	try:
		return InterpretationResult(
			summary=final_state["summary"],
			value_breakdown=_to_value_breakdown(final_state["value_breakdown"]),
			suggested_questions=final_state["suggested_questions"],
			risk_level=final_state["risk_level"],
			confidence=final_state["confidence"],
		)
	except KeyError as exc:
		logger.exception("AI interpretation graph completed with missing fields: %s", exc)
		raise InterpretationError("AI interpretation produced an incomplete result.") from exc


def generate_chat_response(*_args: Any, **_kwargs: Any) -> None:
	"""Stub for the future patient-facing chat surface.

	Intentionally not implemented yet. The Stage 5B scope-cut moves the
	conversational follow-up endpoint out of this milestone — see the RFC
	change log. Calling this raises so accidental wiring fails loudly.
	"""
	raise NotImplementedError(
		"generate_chat_response is deferred. See RFC change log (Stage 5B) for rationale.",
	)
