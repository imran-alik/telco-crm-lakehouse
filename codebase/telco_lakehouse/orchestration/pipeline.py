from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import duckdb
from pydantic import ValidationError

from telco_lakehouse.config.settings import LakehouseConfig
from telco_lakehouse.governance.masking import apply_legal_mask
from telco_lakehouse.orchestration.sql_loader import load_layer_sql, load_layer_sql_batch
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

    def _sql_prefixes(self) -> dict[str, str]:
        return {
            "bronze_prefix": self.config.bronze_prefix,
            "silver_prefix": self.config.silver_prefix,
            "gold_prefix": self.config.gold_prefix,
            "mart_prefix": self.config.mart_prefix,
        }

    def run_silver(self) -> dict[str, int]:
        """3NF normalized staging — FK-ready entities."""
        prefixes = self._sql_prefixes()
        statements = load_layer_sql_batch(
            "silver",
            ["customer.sql", "agent.sql", "call.sql", "offer_event.sql", "intent.sql"],
            **prefixes,
        )
        counts: dict[str, int] = {}
        for sql in statements:
            self.conn.execute(sql)
        for table in ("customer", "agent", "call", "offer_event", "intent"):
            t = f"{self.config.silver_prefix}{table}"
            counts[table] = int(self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
        return counts

    def run_gold(self) -> dict[str, int]:
        """Star schema: dimensions + facts."""
        prefixes = self._sql_prefixes()
        for filename in (
            "dim_customer.sql",
            "dim_agent.sql",
            "dim_disposition.sql",
            "dim_channel.sql",
            "dim_offer.sql",
            "dim_date.sql",
            "fact_call.sql",
            "fact_offer.sql",
        ):
            self.conn.execute(load_layer_sql("gold", filename, **prefixes))
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
            counts[t] = int(
                self.conn.execute(f"SELECT COUNT(*) FROM {self.config.gold_prefix}{t}").fetchone()[
                    0
                ]
            )
        return counts

    def run_marts(self) -> dict[str, int]:
        prefixes = self._sql_prefixes()
        self.conn.execute(load_layer_sql("marts", "finance.sql", **prefixes))
        raw_legal_query = load_layer_sql("marts", "legal.sql", **prefixes)
        raw_legal = self.conn.execute(raw_legal_query).fetchall()
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
        self.conn.execute(load_layer_sql("marts", "ml_features.sql", **prefixes))
        return {
            "mart_finance_revenue": int(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {self.config.mart_prefix}finance_revenue"
                ).fetchone()[0]
            ),
            "mart_legal_compliance": int(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {self.config.mart_prefix}legal_compliance"
                ).fetchone()[0]
            ),
            "mart_ml_features": int(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {self.config.mart_prefix}ml_features"
                ).fetchone()[0]
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
