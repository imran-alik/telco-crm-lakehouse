from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import duckdb
from pydantic import ValidationError

from telco_lakehouse.config.settings import LakehouseConfig
from telco_lakehouse.governance.masking import apply_legal_mask
from telco_lakehouse.quality.dlq import DeadLetterQueue
from telco_lakehouse.schemas import (
    AgentRecord,
    CallCdrRecord,
    CustomerCrmRecord,
    DemographicsRecord,
    IntentLabelRecord,
    OfferDispositionRecord,
)

log = logging.getLogger(__name__)

SAMPLE_FILES = {
    "customers_crm": CustomerCrmRecord,
    "agents": AgentRecord,
    "calls": CallCdrRecord,
    "offers_disposition": OfferDispositionRecord,
    "intent_labels": IntentLabelRecord,
    "demographics": DemographicsRecord,
}


class TelcoLakehousePipeline:
    """Medallion pipeline: bronze CSV ingest → silver 3NF → gold star → consumer marts."""

    def __init__(self, config: LakehouseConfig) -> None:
        config.ensure_dirs()
        self.config = config
        self.dlq = DeadLetterQueue(config.dlq_dir)
        self.conn = duckdb.connect(config.db_path)
        self._configure()
        self.rows_ingested: dict[str, int] = {}

    def _configure(self) -> None:
        self.conn.execute("SET memory_limit='2GB'")
        self.conn.execute("SET threads=4")

    def _load_csv_to_bronze(self, name: str, model: type) -> int:
        path = Path(self.config.samples_dir) / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Sample not found: {path}")
        table = f"{self.config.bronze_prefix}{name}"
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                coerced = {k: (None if v == "" else v) for k, v in raw.items()}
                if "agent_id" in coerced and coerced["agent_id"] == "":
                    coerced["agent_id"] = None
                try:
                    validated = model(**coerced)
                    rows.append(validated.model_dump())
                except (ValidationError, ValueError) as exc:
                    self.dlq.route(name, raw, str(exc))
        if not rows:
            return 0
        cols = list(rows[0].keys())
        col_defs = ", ".join(f"{c} VARCHAR" for c in cols)
        self.conn.execute(f"CREATE OR REPLACE TABLE {table} ({col_defs})")
        placeholders = ", ".join(["?"] * len(cols))
        self.conn.executemany(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            [tuple(str(r[c]) if r[c] is not None else None for c in cols) for r in rows],
        )
        count = int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        self.rows_ingested[name] = count
        log.info("[BRONZE] %s rows=%s", table, count)
        return count

    def run_bronze(self) -> dict[str, int]:
        for name, model in SAMPLE_FILES.items():
            self._load_csv_to_bronze(name, model)
        return dict(self.rows_ingested)

    def run_silver(self) -> dict[str, int]:
        """3NF normalized staging — FK-ready entities."""
        statements = [
            f"""
            CREATE OR REPLACE TABLE {self.config.silver_prefix}customer AS
            SELECT
                c.customer_id,
                c.account_num,
                c.party_type,
                c.segment,
                c.tenure_months,
                c.status,
                c.email_domain,
                d.region,
                d.age_band,
                d.plan_tier
            FROM {self.config.bronze_prefix}customers_crm c
            LEFT JOIN {self.config.bronze_prefix}demographics d USING (customer_id)
            """,
            f"""
            CREATE OR REPLACE TABLE {self.config.silver_prefix}agent AS
            SELECT * FROM {self.config.bronze_prefix}agents
            """,
            f"""
            CREATE OR REPLACE TABLE {self.config.silver_prefix}call AS
            SELECT * FROM {self.config.bronze_prefix}calls
            """,
            f"""
            CREATE OR REPLACE TABLE {self.config.silver_prefix}offer_event AS
            SELECT * FROM {self.config.bronze_prefix}offers_disposition
            """,
            f"""
            CREATE OR REPLACE TABLE {self.config.silver_prefix}intent AS
            SELECT * FROM {self.config.bronze_prefix}intent_labels
            """,
        ]
        counts: dict[str, int] = {}
        for sql in statements:
            self.conn.execute(sql)
        for table in ("customer", "agent", "call", "offer_event", "intent"):
            t = f"{self.config.silver_prefix}{table}"
            counts[table] = int(self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
        return counts

    def run_gold(self) -> dict[str, int]:
        """Star schema: dimensions + facts."""
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_customer AS
            SELECT
                customer_id AS customer_key,
                account_num, party_type, segment, tenure_months, status,
                region, age_band, plan_tier
            FROM {self.config.silver_prefix}customer
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_agent AS
            SELECT agent_id AS agent_key, agent_name, team, skill_group, site_id, hire_date
            FROM {self.config.silver_prefix}agent
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_disposition AS
            SELECT DISTINCT
                disposition_code AS disposition_key,
                disposition_code,
                CASE WHEN disposition_code IN ('ANSWERED','TRANSFER') THEN TRUE ELSE FALSE END AS is_resolution
            FROM {self.config.silver_prefix}call
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_channel AS
            SELECT DISTINCT channel AS channel_key, channel FROM {self.config.silver_prefix}call
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_offer AS
            SELECT DISTINCT offer_id AS offer_key, offer_id, campaign
            FROM {self.config.silver_prefix}offer_event
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}dim_date AS
            SELECT DISTINCT
                CAST(start_time AS TIMESTAMP)::DATE AS date_key,
                CAST(start_time AS TIMESTAMP)::DATE AS call_date,
                EXTRACT(dow FROM CAST(start_time AS TIMESTAMP)) AS day_of_week
            FROM {self.config.silver_prefix}call
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}fact_call AS
            SELECT
                c.call_id,
                c.customer_id AS customer_key,
                c.agent_id AS agent_key,
                c.disposition_code AS disposition_key,
                c.channel AS channel_key,
                CAST(c.start_time AS TIMESTAMP)::DATE AS date_key,
                c.talk_seconds, c.hold_seconds, c.wrap_seconds,
                c.queue_name, c.ani_hash
            FROM {self.config.silver_prefix}call c
            """
        )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.gold_prefix}fact_offer AS
            SELECT
                o.offer_event_id,
                o.call_id,
                o.offer_id AS offer_key,
                o.response,
                o.revenue_usd,
                c.customer_id AS customer_key
            FROM {self.config.silver_prefix}offer_event o
            JOIN {self.config.silver_prefix}call c ON o.call_id = c.call_id
            """
        )
        counts = {}
        for t in (
            "dim_customer",
            "dim_agent",
            "dim_disposition",
            "dim_channel",
            "dim_offer",
            "dim_date",
            "fact_call",
            "fact_offer",
        ):
            counts[t] = int(self.conn.execute(f"SELECT COUNT(*) FROM {self.config.gold_prefix}{t}").fetchone()[0])
        return counts

    def run_marts(self) -> dict[str, int]:
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.mart_prefix}finance_revenue AS
            SELECT
                CAST(c.start_time AS TIMESTAMP)::DATE AS revenue_date,
                cu.segment,
                o.campaign,
                COUNT(DISTINCT o.offer_event_id) AS offer_events,
                SUM(CASE WHEN o.response = 'Accepted' THEN CAST(o.revenue_usd AS DOUBLE) ELSE 0.0 END) AS revenue_usd,
                ROUND(100.0 * SUM(CASE WHEN o.response = 'Accepted' THEN 1 ELSE 0 END)
                      / NULLIF(COUNT(*), 0), 2) AS conversion_pct
            FROM {self.config.bronze_prefix}offers_disposition o
            JOIN {self.config.bronze_prefix}calls c ON o.call_id = c.call_id
            JOIN {self.config.bronze_prefix}customers_crm cu ON c.customer_id = cu.customer_id
            GROUP BY 1, 2, 3
            """
        )
        raw_legal = self.conn.execute(
            f"""
            SELECT call_id, customer_id, agent_id, channel, disposition_code,
                   start_time, ani_hash, queue_name
            FROM {self.config.bronze_prefix}calls
            """
        ).fetchall()
        masked_records = [
            apply_legal_mask(
                dict(
                    zip(
                        [
                            "call_id",
                            "customer_id",
                            "agent_id",
                            "channel",
                            "disposition_code",
                            "start_time",
                            "ani_hash",
                            "queue_name",
                        ],
                        row,
                        strict=True,
                    )
                )
            )
            for row in raw_legal
        ]
        cols = [
            "call_id",
            "customer_id",
            "agent_id",
            "channel",
            "disposition_code",
            "start_time",
            "ani_hash",
            "queue_name",
        ]
        self.conn.execute(
            f"CREATE OR REPLACE TABLE {self.config.mart_prefix}legal_compliance "
            f"({', '.join(f'{c} VARCHAR' for c in cols)})"
        )
        if masked_records:
            self.conn.executemany(
                f"INSERT INTO {self.config.mart_prefix}legal_compliance ({', '.join(cols)}) "
                f"VALUES ({', '.join(['?'] * len(cols))})",
                [tuple(r[c] for c in cols) for r in masked_records],
            )
        self.conn.execute(
            f"""
            CREATE OR REPLACE TABLE {self.config.mart_prefix}ml_features AS
            SELECT
                cu.customer_id,
                cu.segment,
                cu.tenure_months,
                d.region,
                d.age_band,
                d.plan_tier,
                COUNT(DISTINCT c.call_id) AS call_count_90d,
                AVG(CAST(i.confidence_score AS DOUBLE)) AS avg_intent_confidence,
                MAX(CASE WHEN c.disposition_code IN ('ANSWERED','TRANSFER') THEN 1 ELSE 0 END) AS had_resolution,
                SUM(CASE WHEN o.response = 'Accepted' THEN CAST(o.revenue_usd AS DOUBLE) ELSE 0.0 END)
                    AS lifetime_offer_revenue
            FROM {self.config.bronze_prefix}customers_crm cu
            LEFT JOIN {self.config.bronze_prefix}demographics d USING (customer_id)
            LEFT JOIN {self.config.bronze_prefix}calls c ON cu.customer_id = c.customer_id
            LEFT JOIN {self.config.bronze_prefix}intent_labels i ON c.call_id = i.call_id
            LEFT JOIN {self.config.bronze_prefix}offers_disposition o ON c.call_id = o.call_id
            GROUP BY 1, 2, 3, 4, 5, 6
            """
        )
        return {
            "mart_finance_revenue": int(
                self.conn.execute(f"SELECT COUNT(*) FROM {self.config.mart_prefix}finance_revenue").fetchone()[0]
            ),
            "mart_legal_compliance": int(
                self.conn.execute(f"SELECT COUNT(*) FROM {self.config.mart_prefix}legal_compliance").fetchone()[0]
            ),
            "mart_ml_features": int(
                self.conn.execute(f"SELECT COUNT(*) FROM {self.config.mart_prefix}ml_features").fetchone()[0]
            ),
        }

    def run_all(self) -> dict[str, Any]:
        bronze = self.run_bronze()
        silver = self.run_silver()
        gold = self.run_gold()
        marts = self.run_marts()
        bronze_total = sum(bronze.values())
        return {
            "bronze": bronze,
            "silver": silver,
            "gold": gold,
            "marts": marts,
            "dlq_files": self.dlq.count(),
            "layer_counts": {
                "bronze_total": bronze_total,
                "silver_total": sum(silver.values()),
                "gold_total": sum(gold.values()),
            },
        }

    def close(self) -> None:
        self.conn.execute("CHECKPOINT")
        self.conn.close()
        self.conn = None  # type: ignore[assignment]
