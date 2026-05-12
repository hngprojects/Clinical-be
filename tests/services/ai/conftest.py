from __future__ import annotations

from typing import Any

import pytest

from app.models.ai_interpretation import Confidence
from app.services.ai.llm_schemas import LLMInterpretation, LLMValueBreakdown


class _FakeStructuredRunnable:
	"""Stands in for the runnable returned by ``chat_model.with_structured_output``.

	``invoke`` returns whatever was queued on the parent fake; if the parent was
	configured to raise, the exception is raised instead.
	"""

	def __init__(self, parent: "FakeChatModel") -> None:
		self._parent = parent

	def invoke(self, _messages: Any) -> LLMInterpretation:
		if self._parent.raise_with is not None:
			raise self._parent.raise_with
		assert self._parent.queued is not None, "FakeChatModel has no queued response"
		return self._parent.queued


class FakeChatModel:
	"""Minimal stand-in for a LangChain ``BaseChatModel`` for our tests.

	Only implements the surface our graph uses: ``with_structured_output(schema)``
	returning a runnable whose ``invoke`` produces the queued response.
	"""

	def __init__(
		self,
		queued: LLMInterpretation | None = None,
		raise_with: Exception | None = None,
	) -> None:
		self.queued = queued
		self.raise_with = raise_with

	def with_structured_output(self, _schema: Any) -> _FakeStructuredRunnable:
		return _FakeStructuredRunnable(self)


@pytest.fixture
def sample_extracted_values() -> dict[str, Any]:
	return {
		"Hemoglobin": {"value": 14.2, "unit": "g/dL", "reference_range": "13.5-17.5"},
		"WBC": {"value": 12.5, "unit": "x10^9/L", "reference_range": "4.0-11.0"},
		"Glucose": {"value": 88, "unit": "mg/dL", "reference_range": "70-99"},
	}


@pytest.fixture
def llm_response_low_risk() -> LLMInterpretation:
	return LLMInterpretation(
		summary="All reported values are within typical reference ranges.",
		value_breakdown=[
			LLMValueBreakdown(metric="Hemoglobin", value="14.2", unit="g/dL", status="normal"),
			LLMValueBreakdown(metric="WBC", value="9.0", unit="x10^9/L", status="normal"),
			LLMValueBreakdown(metric="Glucose", value="88", unit="mg/dL", status="normal"),
		],
		suggested_questions=[
			"Are there any follow-up tests I should consider?",
			"How often should I repeat this panel?",
		],
		confidence=Confidence.HIGH,
	)


@pytest.fixture
def llm_response_moderate_risk() -> LLMInterpretation:
	return LLMInterpretation(
		summary="Most values look typical; one is slightly outside the usual range.",
		value_breakdown=[
			LLMValueBreakdown(metric="Hemoglobin", value="14.2", unit="g/dL", status="normal"),
			LLMValueBreakdown(metric="WBC", value="12.5", unit="x10^9/L", status="caution"),
			LLMValueBreakdown(metric="Glucose", value="88", unit="mg/dL", status="normal"),
		],
		suggested_questions=["What could a mildly elevated WBC suggest?"],
		confidence=Confidence.MEDIUM,
	)


@pytest.fixture
def llm_response_high_risk() -> LLMInterpretation:
	return LLMInterpretation(
		summary="Several values fall outside typical reference ranges and warrant a clinician's review.",
		value_breakdown=[
			LLMValueBreakdown(metric="Hemoglobin", value="8.0", unit="g/dL", status="abnormal"),
			LLMValueBreakdown(metric="WBC", value="12.5", unit="x10^9/L", status="caution"),
			LLMValueBreakdown(metric="Glucose", value="88", unit="mg/dL", status="normal"),
		],
		suggested_questions=["What might explain a low hemoglobin reading?"],
		confidence=Confidence.MEDIUM,
	)
