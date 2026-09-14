from __future__ import annotations

from pydantic import BaseModel, field_validator

VALID_REGIONS = frozenset({"Northeast", "Southeast", "Midwest", "West"})
VALID_AGE_BANDS = frozenset({"18-24", "25-34", "35-44", "45-54", "55-64", "65+"})
VALID_PLAN_TIERS = frozenset({"Basic", "Plus", "Premium", "Fiber"})


class DemographicsRecord(BaseModel):
    """Customer demographic enrichment keyed by CRM customer_id."""

    customer_id: str
    region: str
    age_band: str
    plan_tier: str

    @field_validator("customer_id")
    @classmethod
    def strip_customer_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("customer_id must not be empty")
        return normalized

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_REGIONS:
            raise ValueError(f"Invalid region: {value}")
        return normalized

    @field_validator("age_band")
    @classmethod
    def validate_age_band(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_AGE_BANDS:
            raise ValueError(f"Invalid age_band: {value}")
        return normalized

    @field_validator("plan_tier")
    @classmethod
    def validate_plan_tier(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_PLAN_TIERS:
            raise ValueError(f"Invalid plan_tier: {value}")
        return normalized
