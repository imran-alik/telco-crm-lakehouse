#!/usr/bin/env python
"""Certified medallion run: full sample ingest, mart proof, quality gates."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))
sys.path.insert(0, str(ROOT / "packages" / "lakehouse_core"))

from core import (
    build_daily_status,
    check_table_freshness,
    evaluate_thresholds,
    guardrails_summary,
    run_failure_checks,
    run_guardrails,
    run_health_check,
    summarize_freshness,
)
from telco_lakehouse.analytics.kpi import compute_kpis, evaluate_alerts
from telco_lakehouse.config.settings import LakehouseConfig, repo_root
from telco_lakehouse.evidence.writer import write_run_summary
from telco_lakehouse.orchestration.pipeline import TelcoLakehousePipeline


def _reset_sink(config: LakehouseConfig) -> None:
    sink = Path(config.db_path).parent
    if sink.exists():
        shutil.rmtree(sink)
    config.ensure_dirs()


def _count_sample_rows(samples_dir: Path) -> int:
    total = 0
    for path in samples_dir.glob("*.csv"):
        with path.open(encoding="utf-8") as handle:
            total += sum(1 for _ in handle) - 1
    return total


def main() -> int:
    config = LakehouseConfig()
    samples = Path(config.samples_dir)
    if not list(samples.glob("*.csv")):
        import subprocess

        subprocess.check_call([sys.executable, str(ROOT / "codebase" / "scripts" / "generate_samples.py")])

    source_rows = _count_sample_rows(samples)
    _reset_sink(config)
    started = time.perf_counter()

    pipeline = TelcoLakehousePipeline(config)
    run_summary = pipeline.run_all()
    kpis = compute_kpis(config.db_path, conn=pipeline.conn)
    alerts = evaluate_alerts(kpis)
    health = run_health_check(pipeline.conn, db_path=config.db_path)
    freshness = summarize_freshness(
        [
            check_table_freshness(pipeline.conn, f"{config.gold_prefix}fact_call"),
            check_table_freshness(pipeline.conn, f"{config.mart_prefix}finance_revenue"),
        ]
    )
    guardrails = guardrails_summary(
        run_guardrails(
            dlq_count=run_summary["dlq_files"],
            bronze_rows=run_summary["layer_counts"]["bronze_total"],
        )
    )
    failure_checks = run_failure_checks(pipeline.conn)
    core_alerts = [a.__dict__ for a in evaluate_thresholds(kpis)]
    daily_status = build_daily_status(
        health=health.__dict__,
        freshness=freshness,
        guardrails=guardrails,
        kpis=kpis,
    )
    pipeline.close()

    pipeline2 = TelcoLakehousePipeline(config)
    replay = pipeline2.run_all()
    pipeline2.close()

    elapsed = round(time.perf_counter() - started, 3)
    certification = {
        "problem": "Telco CRM medallion lakehouse with governed consumer marts",
        "source": {
            "name": "Synthetic telco CRM/contact-center samples",
            "directory": str(samples.relative_to(repo_root())).replace("\\", "/"),
            "source_rows_in_files": source_rows,
            "alignment_references": ["Cisco CDR", "Genesis ACD", "Siebel CRM", "Oracle CRM"],
        },
        "pipeline": run_summary,
        "kpis": kpis,
        "alerts": alerts,
        "operations": {
            "health": health.__dict__,
            "freshness": freshness,
            "guardrails": guardrails,
            "failure_checks": failure_checks,
            "core_alerts": core_alerts,
            "daily_status": daily_status,
        },
        "quality_gates": {
            "bronze_ingested": run_summary["layer_counts"]["bronze_total"] > 0,
            "silver_built": run_summary["layer_counts"]["silver_total"] > 0,
            "gold_built": run_summary["layer_counts"]["gold_total"] > 0,
            "finance_mart_built": run_summary["marts"]["mart_finance_revenue"] >= 1,
            "legal_mart_built": run_summary["marts"]["mart_legal_compliance"] >= 1,
            "ml_mart_built": run_summary["marts"]["mart_ml_features"] >= 1,
            "dlq_zero_on_sample": run_summary["dlq_files"] == 0,
            "idempotent_replay_stable": replay["layer_counts"]["bronze_total"]
            == run_summary["layer_counts"]["bronze_total"],
            "call_resolution_kpi_computed": kpis["call_resolution_pct"] > 0,
            "offer_revenue_computed": kpis["total_offer_revenue_usd"] > 0,
            "guardrails_passed": guardrails["passed"],
            "failure_checks_passed": failure_checks["passed"],
            "health_ok": health.status == "healthy",
        },
        "replay": replay,
        "timing_seconds": elapsed,
    }

    artifact = write_run_summary(
        evidence_dir=repo_root() / "data" / "evidence",
        run_name="telco_full_sample",
        payload=certification,
    )
    print(json.dumps({"artifact": str(artifact), **certification}, indent=2, default=str))

    failed = [k for k, v in certification["quality_gates"].items() if not v]
    if failed:
        print(f"QUALITY GATE FAILURES: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
