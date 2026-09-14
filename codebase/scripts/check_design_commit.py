#!/usr/bin/env python
"""Static gates from docs/standards/design-commit.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "README.md",
    "SOLUTION.md",
    "CHANGELOG.md",
    "data-dictionary.md",
    "docs/DESIGN.md",
    "docs/HANDOVER.md",
    "docs/databricks/DATABRICKS-SERVICES.md",
    "docs/CONNECTIVITY.md",
    "docs/LIBRARIES.md",
    "commands.txt",
    "analytics_query.sql",
    "codebase/requirements-runtime.txt",
    "codebase/scripts/bootstrap.ps1",
    "codebase/scripts/HOW-TO-EXECUTE.md",
    "codebase/scripts/certify_public_run.py",
    "docs/standards/data-engineering-design-standards.md",
    "docs/standards/design-patterns.md",
    "docs/standards/design-commit.md",
    "data/evidence/run_summary_index.json",
    "docker-compose.yml",
    "Dockerfile",
    "tests/test_pipeline.py",
    "tests/test_certification.py",
]

REQUIRED_MODULES = [
    "codebase/telco_lakehouse/config/settings.py",
    "codebase/telco_lakehouse/orchestration/pipeline.py",
    "codebase/telco_lakehouse/governance/masking.py",
    "codebase/telco_lakehouse/analytics/kpi.py",
    "codebase/telco_lakehouse/evidence/writer.py",
    "codebase/telco_lakehouse/quality/dlq.py",
]

DESIGN_HEADINGS = [
    "Verdicts",
    "Problem statement",
    "Ask register",
    "Sources and sinks",
    "Lineage",
    "Failure matrix",
    "Test plan",
    "Module map",
    "Document control",
]

BANNED_README = ["plug and play", "plug-and-play"]


def main() -> int:
    failures: list[str] = []
    for rel in REQUIRED_FILES + REQUIRED_MODULES:
        if not (ROOT / rel).exists():
            failures.append(f"Missing required path: {rel}")

    design = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    for heading in DESIGN_HEADINGS:
        if heading.lower() not in design.lower():
            failures.append(f"DESIGN.md missing section keyword: {heading}")

    solution = (ROOT / "SOLUTION.md").read_text(encoding="utf-8")
    design_asks = set(re.findall(r"\*\*A(\d+)\*\*", design))
    solution_asks = set(re.findall(r"## A(\d+)", solution))
    if design_asks and design_asks != solution_asks:
        failures.append(
            f"Ask ID drift DESIGN {sorted(design_asks)} vs SOLUTION {sorted(solution_asks)}"
        )

    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for token in BANNED_README:
        if token in readme:
            failures.append(f"README.md contains banned phrase: {token}")

    if failures:
        print("DESIGN-COMMIT STATIC CHECK FAILED:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print("Design-commit static checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
