from __future__ import annotations

from pydantic import BaseModel, field_validator

VALID_CHANNELS = frozenset({"voice", "chat", "callback"})
VALID_DISPOSITIONS = frozenset(
    {"ANSWERED", "ABANDONED", "TRANSFER", "VOICEMAIL", "CALLBACK_SCHEDULED"}
)


class CallCdrRecord(BaseModel):
    """Cisco Unified Contact Center CDR-style contract."""

    call_id: str
    customer_id: str
    agent_id: str | None
    ani_hash: str
    dnis: str
    channel: str
    queue_name: str
    start_time: str
    talk_seconds: int
    hold_seconds: int
    disposition_code: str
    wrap_seconds: int

    @field_validator("call_id", "customer_id", "ani_hash", "dnis", "queue_name", "start_time")
    @classmethod
    def strip_required(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field must not be empty")
        return normalized

    @field_validator("agent_id", mode="before")
    @classmethod
    def empty_agent_to_none(cls, value: object) -> object:
        if value is None:
            return None
        text = str(value).strip()
        if text.lower() in {"", "null", "none", "nan"}:
            return None
        return text

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel: {value}")
        return normalized

    @field_validator("disposition_code")
    @classmethod
    def validate_disposition(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in VALID_DISPOSITIONS:
            raise ValueError(f"Invalid disposition_code: {value}")
        return normalized

    @field_validator("talk_seconds", "hold_seconds", "wrap_seconds")
    @classmethod
    def validate_non_negative_duration(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Duration seconds must be >= 0")
        return value

    @field_validator("ani_hash")
    @classmethod
    def validate_ani_hash(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
            raise ValueError("ani_hash must be a 64-char lowercase hex SHA-256 digest")
        return normalized
