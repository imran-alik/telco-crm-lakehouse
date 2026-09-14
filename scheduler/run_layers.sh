#!/bin/sh
# Sequential medallion layer runner — bronze → silver → gold → marts; exit on first failure.
set -eu

cd "$(dirname "$0")/.." || exit 1

run_layer() {
  layer="$1"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] layer=${layer}"
  LAYER="${layer}" python - <<'PY'
import os
import sys

from telco_lakehouse.config.settings import LakehouseConfig
from telco_lakehouse.orchestration.pipeline import TelcoLakehousePipeline

layer = os.environ["LAYER"]
config = LakehouseConfig()
pipeline = TelcoLakehousePipeline(config)
dispatch = {
    "bronze": pipeline.run_bronze,
    "silver": pipeline.run_silver,
    "gold": pipeline.run_gold,
    "marts": pipeline.run_marts,
}
try:
    runner = dispatch.get(layer)
    if runner is None:
        print(f"unknown layer: {layer}", file=sys.stderr)
        sys.exit(1)
    counts = runner()
    print(f"layer={layer} counts={counts}")
finally:
    pipeline.close()
PY
}

run_layer bronze
run_layer silver
run_layer gold
run_layer marts
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] all layers complete"
