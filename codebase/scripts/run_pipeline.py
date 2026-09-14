#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from telco_lakehouse.config.settings import LakehouseConfig
from telco_lakehouse.orchestration.pipeline import TelcoLakehousePipeline


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Run telco CRM lakehouse pipeline")
    parser.add_argument(
        "--layer", choices=["bronze", "silver", "gold", "marts", "all"], default="all"
    )
    args = parser.parse_args()

    config = LakehouseConfig()
    pipeline = TelcoLakehousePipeline(config)
    try:
        if args.layer == "bronze":
            summary = {"bronze": pipeline.run_bronze()}
        elif args.layer == "silver":
            pipeline.run_bronze()
            summary = {"silver": pipeline.run_silver()}
        elif args.layer == "gold":
            pipeline.run_bronze()
            pipeline.run_silver()
            summary = {"gold": pipeline.run_gold()}
        elif args.layer == "marts":
            pipeline.run_bronze()
            pipeline.run_silver()
            pipeline.run_gold()
            summary = {"marts": pipeline.run_marts()}
        else:
            summary = pipeline.run_all()
        print(json.dumps(summary, indent=2, default=str))
    finally:
        pipeline.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
