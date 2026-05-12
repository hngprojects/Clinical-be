from typing import Literal

from pydantic import BaseModel, Field

from app.models.ai_interpretation import Confidence

ValueStatus = Literal["normal", "caution", "abnormal"]


class LLMValueBreakdown(BaseModel):
	"""One classified lab metric produced by the LLM."""

	metric: str = Field(description="Canonical name of the lab metric, e.g. 'Hemoglobin'.")
	value: str = Field(description="Reported value as a string, preserving the original units when possible.")
	unit: str | None = Field(default=None, description="Unit of measurement, e.g. 'g/dL'. Null if not provided.")
	status: ValueStatus = Field(description="Classification of the value relative to a typical reference range.")
	note: str | None = Field(
		default=None,
		description="Short, plain-language observation about the value. Must not contain a diagnosis or treatment advice.",
	)


class LLMInterpretation(BaseModel):
	"""Structured output contract that the LLM must return."""

	summary: str = Field(
		description=(
			"Two-to-four-sentence plain-language overview of the results. Describe what was observed in neutral, "
			"non-diagnostic language. Do not recommend treatments or claim to diagnose conditions."
		),
	)
	value_breakdown: list[LLMValueBreakdown] = Field(
		description="One entry per lab value provided in the input, in the same order when reasonable.",
	)
	suggested_questions: list[str] = Field(
		description=(
			"Three to five questions the patient could ask their doctor. Questions only — no answers, no advice."
		),
	)
	confidence: Confidence = Field(
		description=(
			"Self-rated confidence of this interpretation. Use 'low' when the input is sparse, ambiguous, or "
			"missing units/reference ranges."
		),
	)
