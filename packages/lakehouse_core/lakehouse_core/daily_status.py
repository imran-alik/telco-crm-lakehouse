from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_daily_status(
    *,
    health: dict[str, Any],
    freshness: dict[str, Any],
    guardrails: dict[str, Any],
    kpis: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_date_utc": datetime.now(UTC).date().isoformat(),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "health": health,
        "freshness": freshness,
        "guardrails": guardrails,
        "kpis": kpis,
        "overall_ok": guardrails.get("passed", False) and not freshness.get("stale_tables"),
    }
