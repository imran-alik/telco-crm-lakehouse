from __future__ import annotations

from pydantic import BaseModel, field_validator

VALID_INTENT_CATEGORIES = frozenset(
    {
        "billing",
        "technical",
        "cancel",
        "upgrade",
        "account_change",
        "outage",
        "general_inquiry",
    }
)


class IntentLabelRecord(BaseModel):
    """NLP intent classification output for a handled interaction."""

    call_id: str
    intent_category: str
    confidence_score: float
    model_version: str

    @field_validator("call_id", "model_version")
    @classmethod
    def strip_required(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field must not be empty")
        return normalized

    @field_validator("intent_category")
    @classmethod
    def validate_intent(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_INTENT_CATEGORIES:
            raise ValueError(f"Invalid intent_category: {value}")
        return normalized

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence_score must be between 0 and 1")
        return value
