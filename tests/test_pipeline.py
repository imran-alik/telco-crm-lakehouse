from __future__ import annotations

import shutil
from pathlib import Path

import duckdb

from telco_lakehouse.analytics.kpi import compute_kpis, evaluate_alerts
from telco_lakehouse.config.settings import LakehouseConfig
from telco_lakehouse.governance.masking import apply_legal_mask, hash_pii
from telco_lakehouse.orchestration.pipeline import TelcoLakehousePipeline


def _copy_samples(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[1] / "data" / "source" / "samples"
    dest = tmp_path / "samples"
    if src.exists():
        shutil.copytree(src, dest)
    else:
        dest.mkdir(parents=True)
        import subprocess
        import sys

        subprocess.check_call(
            [sys.executable, "codebase/scripts/generate_samples.py"], cwd=Path(__file__).parents[1]
        )
        shutil.copytree(src, dest)
    return dest


def test_hash_pii_is_deterministic() -> None:
    assert hash_pii("5551234567") == hash_pii("5551234567")
    assert hash_pii("5551234567") != hash_pii("5551234568")


def test_legal_mask_hashes_ani() -> None:
    masked = apply_legal_mask({"ani_hash": "abc123", "email_domain": "corp.example.com"})
    assert masked["ani_hash"].startswith("HASH_")
    assert "masked" in str(masked.get("email_domain", ""))


def test_full_medallion_pipeline(tmp_path: Path) -> None:
    samples = _copy_samples(tmp_path)
    config = LakehouseConfig.for_tests(tmp_path, samples_dir=str(samples))

    pipeline = TelcoLakehousePipeline(config)
    summary = pipeline.run_all()
    pipeline.close()

    assert summary["layer_counts"]["bronze_total"] > 1000
    assert summary["marts"]["mart_finance_revenue"] >= 1
    assert summary["marts"]["mart_ml_features"] == 300
    assert summary["dlq_files"] == 0

    kpis = compute_kpis(config.db_path)
    assert kpis["total_calls"] == 1500
    assert kpis["total_offer_revenue_usd"] > 0
    alerts = evaluate_alerts(kpis)
    assert isinstance(alerts, list)


def test_idempotent_replay(tmp_path: Path) -> None:
    samples = _copy_samples(tmp_path)
    config = LakehouseConfig.for_tests(tmp_path, samples_dir=str(samples))

    p1 = TelcoLakehousePipeline(config)
    first = p1.run_all()
    p1.close()

    p2 = TelcoLakehousePipeline(config)
    second = p2.run_all()
    p2.close()

    assert first["layer_counts"]["bronze_total"] == second["layer_counts"]["bronze_total"]


def test_gold_star_tables_exist(tmp_path: Path) -> None:
    samples = _copy_samples(tmp_path)
    config = LakehouseConfig.for_tests(tmp_path, samples_dir=str(samples))

    pipeline = TelcoLakehousePipeline(config)
    pipeline.run_all()
    pipeline.close()

    conn = duckdb.connect(str(tmp_path / "lakehouse.db"), read_only=True)
    dims = conn.execute("SELECT COUNT(*) FROM gold_dim_customer").fetchone()[0]
    facts = conn.execute("SELECT COUNT(*) FROM gold_fact_call").fetchone()[0]
    conn.close()
    assert dims == 300
    assert facts == 1500
