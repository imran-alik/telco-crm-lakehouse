from __future__ import annotations

from typing import Any

import duckdb


def compute_kpis(db_path: str, *, conn: duckdb.DuckDBPyConnection | None = None) -> dict[str, Any]:
    owns_conn = conn is None
    if conn is None:
        conn = duckdb.connect(db_path, read_only=True)
    try:
        total_calls = conn.execute("SELECT COUNT(*) FROM gold_fact_call").fetchone()[0]
        resolved = conn.execute(
            """
            SELECT COUNT(*) FROM gold_fact_call f
            JOIN gold_dim_disposition d ON f.disposition_key = d.disposition_key
            WHERE d.is_resolution = TRUE
            """
        ).fetchone()[0]
        offer_conv = conn.execute(
            """
            SELECT ROUND(100.0 * SUM(CASE WHEN response = 'Accepted' THEN 1 ELSE 0 END)
                   / NULLIF(COUNT(*), 0), 2)
            FROM bronze_offers_disposition
            """
        ).fetchone()[0]
        revenue = conn.execute(
            "SELECT ROUND(COALESCE(SUM(CAST(revenue_usd AS DOUBLE)), 0), 2) "
            "FROM bronze_offers_disposition WHERE response = 'Accepted'"
        ).fetchone()[0]
        agent_util = conn.execute(
            """
            SELECT ROUND(AVG(CAST(talk_seconds AS INTEGER) + CAST(wrap_seconds AS INTEGER)) / 3600.0, 4)
            FROM bronze_calls WHERE agent_id IS NOT NULL
            """
        ).fetchone()[0]
        return {
            "total_calls": int(total_calls),
            "call_resolution_pct": round(100.0 * resolved / max(total_calls, 1), 2),
            "offer_conversion_pct": float(offer_conv or 0),
            "total_offer_revenue_usd": float(revenue or 0),
            "avg_agent_hours_per_call": float(agent_util or 0),
        }
    finally:
        if owns_conn:
            conn.close()


def evaluate_alerts(
    kpis: dict[str, Any], *, resolution_threshold: float = 70.0
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if kpis["call_resolution_pct"] < resolution_threshold:
        alerts.append(
            {
                "alert_type": "LOW_CALL_RESOLUTION",
                "severity": "warning",
                "metric_value": kpis["call_resolution_pct"],
                "threshold": resolution_threshold,
            }
        )
    if kpis["offer_conversion_pct"] < 10.0:
        alerts.append(
            {
                "alert_type": "LOW_OFFER_CONVERSION",
                "severity": "info",
                "metric_value": kpis["offer_conversion_pct"],
                "threshold": 10.0,
            }
        )
    return alerts
