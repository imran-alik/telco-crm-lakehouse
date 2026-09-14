from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, field_validator

VALID_RESPONSES = frozenset({"Accepted", "Declined", "No Response"})


class OfferDispositionRecord(BaseModel):
    """Campaign offer outcome tied to a contact-center interaction."""

    offer_event_id: str
    call_id: str
    offer_id: str
    campaign: str
    response: str
    revenue_usd: float

    @field_validator("offer_event_id", "call_id", "offer_id", "campaign")
    @classmethod
    def strip_required(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field must not be empty")
        return normalized

    @field_validator("response")
    @classmethod
    def validate_response(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_RESPONSES:
            raise ValueError(f"Invalid response: {value}")
        return normalized

    @field_validator("revenue_usd")
    @classmethod
    def validate_revenue(cls, value: float) -> float:
        if value < 0:
            raise ValueError("revenue_usd must be >= 0")
        return value

    @property
    def revenue_decimal(self) -> Decimal:
        return Decimal(str(self.revenue_usd))
