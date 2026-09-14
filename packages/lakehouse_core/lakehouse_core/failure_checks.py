from __future__ import annotations

from typing import Any

import duckdb


def run_failure_checks(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Lightweight post-run failure probes."""
    checks: dict[str, bool] = {}
    for table in ("gold_fact_call", "mart_finance_revenue", "mart_ml_features"):
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            checks[f"{table}_non_empty"] = int(count) > 0
        except duckdb.CatalogException:
            checks[f"{table}_non_empty"] = False
    return {"checks": checks, "passed": all(checks.values())}
