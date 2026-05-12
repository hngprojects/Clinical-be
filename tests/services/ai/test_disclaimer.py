from app.services.ai.disclaimer import DISCLAIMER, with_disclaimer


def test_disclaimer_is_non_empty():
	assert DISCLAIMER.strip(), "Disclaimer placeholder must not be empty"


def test_with_disclaimer_prepends_to_summary():
	result = with_disclaimer("Values look typical.")
	assert result.startswith(DISCLAIMER)
	assert "Values look typical." in result


def test_with_disclaimer_handles_empty_summary():
	assert with_disclaimer("") == DISCLAIMER
	assert with_disclaimer("   ") == DISCLAIMER


def test_with_disclaimer_strips_summary_whitespace():
	result = with_disclaimer("  hello  ")
	assert result.endswith("hello")
