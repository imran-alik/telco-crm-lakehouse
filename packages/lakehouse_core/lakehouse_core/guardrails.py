from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GuardrailResult:
    name: str
    passed: bool
    detail: str


def run_guardrails(
    *, dlq_count: int, bronze_rows: int, min_bronze: int = 100
) -> list[GuardrailResult]:
    return [
        GuardrailResult(
            name="dlq_zero_on_certified_sample",
            passed=dlq_count == 0,
            detail=f"dlq_count={dlq_count}",
        ),
        GuardrailResult(
            name="bronze_minimum_volume",
            passed=bronze_rows >= min_bronze,
            detail=f"bronze_rows={bronze_rows}",
        ),
    ]


def guardrails_summary(results: list[GuardrailResult]) -> dict[str, Any]:
    return {
        "passed": all(r.passed for r in results),
        "checks": [{"name": r.name, "passed": r.passed, "detail": r.detail} for r in results],
    }
