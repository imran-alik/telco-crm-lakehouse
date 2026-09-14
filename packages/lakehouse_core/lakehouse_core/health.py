from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import duckdb


@dataclass(frozen=True)
class HealthReport:
    status: str
    db_path: str
    table_count: int
    checked_at_utc: str
    details: dict[str, Any]


def run_health_check(conn: duckdb.DuckDBPyConnection, *, db_path: str) -> HealthReport:
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    status = "healthy" if table_names else "degraded"
    return HealthReport(
        status=status,
        db_path=db_path,
        table_count=len(table_names),
        checked_at_utc=datetime.now(UTC).isoformat(),
        details={"tables": table_names[:20]},
    )
