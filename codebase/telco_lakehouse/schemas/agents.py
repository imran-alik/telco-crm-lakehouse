from __future__ import annotations

from datetime import date

from pydantic import BaseModel, field_validator

VALID_TEAMS = frozenset({"Sales", "Retention", "Support", "Billing"})
VALID_SKILL_GROUPS = frozenset({"Spanish", "Technical", "Premium", "General"})


class AgentRecord(BaseModel):
    """Genesis ACD agent roster contract."""

    agent_id: str
    agent_name: str
    team: str
    skill_group: str
    site_id: str
    hire_date: date

    @field_validator("agent_id", "agent_name", "site_id")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field must not be empty")
        return normalized

    @field_validator("team")
    @classmethod
    def validate_team(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_TEAMS:
            raise ValueError(f"Invalid team: {value}")
        return normalized

    @field_validator("skill_group")
    @classmethod
    def validate_skill_group(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in VALID_SKILL_GROUPS:
            raise ValueError(f"Invalid skill_group: {value}")
        return normalized
