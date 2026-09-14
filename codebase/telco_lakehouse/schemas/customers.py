from __future__ import annotations

from pydantic import BaseModel, field_validator

VALID_PARTY_TYPES = frozenset({"Individual", "Organization"})
VALID_SEGMENTS = frozenset({"Consumer", "SMB", "Enterprise"})
VALID_STATUSES = frozenset({"Active", "Suspended", "Closed"})


class CustomerCrmRecord(BaseModel):
    """Siebel / Oracle CRM party-account contract."""

    customer_id: str
    account_num: str
    party_type: str
    segment: str
    tenure_months: int
    status: str
    email_domain: str

    @field_validator("customer_id", "account_num")
    @classmethod
    def strip_required_ids(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Identifier must not be empty")
        return normalized

    @field_validator("party_type")
    @classmethod
    def validate_party_type(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_PARTY_TYPES:
            raise ValueError(f"Invalid party_type: {value}")
        return normalized

    @field_validator("segment")
    @classmethod
    def validate_segment(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_SEGMENTS:
            raise ValueError(f"Invalid segment: {value}")
        return normalized

    @field_validator("tenure_months")
    @classmethod
    def validate_tenure(cls, value: int) -> int:
        if value < 0:
            raise ValueError("tenure_months must be >= 0")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        return normalized

    @field_validator("email_domain")
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "." not in normalized or normalized.startswith("."):
            raise ValueError(f"Invalid email_domain: {value}")
        return normalized
