from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def write_run_summary(*, evidence_dir: str | Path, run_name: str, payload: dict[str, Any]) -> Path:
    target = Path(evidence_dir)
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = target / f"run_summary_{run_name}_{stamp}.json"
    envelope = {"generated_at_utc": datetime.now(UTC).isoformat(), "run_name": run_name, **payload}
    path.write_text(json.dumps(envelope, indent=2, default=str), encoding="utf-8")
    index_path = target / "run_summary_index.json"
    index = {"runs": []}
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    index["runs"].append(
        {
            "run_name": run_name,
            "artifact": path.name,
            "generated_at_utc": envelope["generated_at_utc"],
            "bronze_rows": payload.get("pipeline", {}).get("layer_counts", {}).get("bronze_total"),
            "mart_finance_rows": payload.get("pipeline", {}).get("marts", {}).get("mart_finance_revenue"),
            "quality_gates_passed": all(payload.get("quality_gates", {}).values()),
        }
    )
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path
