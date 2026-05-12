import json
import logging
from typing import Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.core.exceptions import InterpretationError
from app.models.ai_interpretation import Confidence, RiskLevel
from app.services.ai.disclaimer import with_disclaimer
from app.services.ai.llm_schemas import LLMInterpretation, LLMValueBreakdown
from app.services.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
	"""Mutable state passed between LangGraph nodes."""

	extracted_values: dict[str, Any]
	chat_model: BaseChatModel
	llm_output: LLMInterpretation
	value_breakdown: list[LLMValueBreakdown]
	summary: str
	suggested_questions: list[str]
	risk_level: RiskLevel
	confidence: Confidence


def _validate_input(state: GraphState) -> GraphState:
	"""Reject empty / non-dict extracted values before they reach the LLM."""
	values = state.get("extracted_values")
	if not isinstance(values, dict) or not values:
		raise InterpretationError("Extracted lab values are empty or malformed.")
	return {}


def _classify_values(state: GraphState) -> GraphState:
	"""Call the LLM with the structured-output contract and capture its response."""
	chat_model = state.get("chat_model")
	if chat_model is None:
		raise InterpretationError("Chat model was not injected into the graph state.")

	values_json = json.dumps(state["extracted_values"], default=str, sort_keys=True)
	messages = [
		SystemMessage(content=SYSTEM_PROMPT),
		HumanMessage(content=USER_PROMPT_TEMPLATE.format(values_json=values_json)),
	]

	structured = chat_model.with_structured_output(LLMInterpretation)

	try:
		result = structured.invoke(messages)
	except Exception as exc:  # noqa: BLE001 - we normalize all LLM failures
		logger.exception("LLM call failed during AI interpretation")
		raise InterpretationError("The AI provider failed to return a valid response.") from exc

	if not isinstance(result, LLMInterpretation):
		raise InterpretationError("AI provider returned an output that did not match the expected schema.")

	return {"llm_output": result}


def _derive_risk(state: GraphState) -> GraphState:
	"""Compute risk level deterministically from the LLM's per-value classifications.

	Risk is intentionally computed in code (not by the LLM) so it is auditable and
	reproducible: any 'abnormal' -> HIGH, otherwise any 'caution' -> MODERATE, else LOW.
	"""
	llm_output = state["llm_output"]
	breakdown = llm_output.value_breakdown or []

	statuses = {item.status for item in breakdown}
	if "abnormal" in statuses:
		risk = RiskLevel.HIGH
	elif "caution" in statuses:
		risk = RiskLevel.MODERATE
	else:
		risk = RiskLevel.LOW

	return {
		"value_breakdown": breakdown,
		"risk_level": risk,
		"confidence": llm_output.confidence,
		"suggested_questions": llm_output.suggested_questions or [],
	}


def _inject_disclaimer(state: GraphState) -> GraphState:
	"""Prepend the medical disclaimer to the LLM summary."""
	raw_summary = state["llm_output"].summary
	return {"summary": with_disclaimer(raw_summary)}


def build_graph():
	"""Compile and return the LangGraph state machine.

	The graph is built lazily on every call rather than module import so unit tests
	can swap nodes or providers cleanly. LangGraph compilation is cheap.
	"""
	graph = StateGraph(GraphState)
	graph.add_node("validate_input", _validate_input)
	graph.add_node("classify_values", _classify_values)
	graph.add_node("derive_risk", _derive_risk)
	graph.add_node("inject_disclaimer", _inject_disclaimer)

	graph.add_edge(START, "validate_input")
	graph.add_edge("validate_input", "classify_values")
	graph.add_edge("classify_values", "derive_risk")
	graph.add_edge("derive_risk", "inject_disclaimer")
	graph.add_edge("inject_disclaimer", END)

	return graph.compile()
