from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import duckdb


@dataclass(frozen=True)
class FreshnessReport:
    table_name: str
    row_count: int
    checked_at_utc: str
    is_stale: bool
    note: str


def check_table_freshness(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    *,
    min_rows: int = 1,
) -> FreshnessReport:
    row_count = int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    is_stale = row_count < min_rows
    return FreshnessReport(
        table_name=table_name,
        row_count=row_count,
        checked_at_utc=datetime.now(UTC).isoformat(),
        is_stale=is_stale,
        note="below minimum row threshold" if is_stale else "ok",
    )


def summarize_freshness(reports: list[FreshnessReport]) -> dict[str, Any]:
    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "tables": [r.__dict__ for r in reports],
        "stale_tables": [r.table_name for r in reports if r.is_stale],
    }
