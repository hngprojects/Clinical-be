import pytest

from app.core.exceptions import InterpretationError
from app.models.ai_interpretation import Confidence, RiskLevel
from app.services.ai import interpret
from app.services.ai.disclaimer import DISCLAIMER


def test_interpret_low_risk_when_all_values_normal(sample_extracted_values, llm_response_low_risk):
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel(queued=llm_response_low_risk)
	result = interpret(sample_extracted_values, chat_model=model)

	assert result.risk_level is RiskLevel.LOW
	assert result.confidence is Confidence.HIGH
	assert result.summary.startswith(DISCLAIMER)
	assert len(result.value_breakdown) == 3
	assert all(item.status == "normal" for item in result.value_breakdown)


def test_interpret_moderate_risk_when_any_caution(sample_extracted_values, llm_response_moderate_risk):
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel(queued=llm_response_moderate_risk)
	result = interpret(sample_extracted_values, chat_model=model)

	assert result.risk_level is RiskLevel.MODERATE


def test_interpret_high_risk_when_any_abnormal(sample_extracted_values, llm_response_high_risk):
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel(queued=llm_response_high_risk)
	result = interpret(sample_extracted_values, chat_model=model)

	assert result.risk_level is RiskLevel.HIGH


def test_interpret_rejects_empty_extracted_values():
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel()
	with pytest.raises(InterpretationError):
		interpret({}, chat_model=model)


def test_interpret_rejects_non_dict_extracted_values():
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel()
	with pytest.raises(InterpretationError):
		interpret("not a dict", chat_model=model)  # type: ignore[arg-type]


def test_interpret_wraps_llm_failures_as_interpretation_error(sample_extracted_values):
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel(raise_with=RuntimeError("upstream provider is down"))
	with pytest.raises(InterpretationError):
		interpret(sample_extracted_values, chat_model=model)


def test_interpret_result_includes_suggested_questions(sample_extracted_values, llm_response_low_risk):
	from tests.services.ai.conftest import FakeChatModel

	model = FakeChatModel(queued=llm_response_low_risk)
	result = interpret(sample_extracted_values, chat_model=model)

	assert isinstance(result.suggested_questions, list)
	assert len(result.suggested_questions) >= 1


def test_generate_chat_response_is_deferred():
	from app.services.ai import generate_chat_response

	with pytest.raises(NotImplementedError):
		generate_chat_response()
