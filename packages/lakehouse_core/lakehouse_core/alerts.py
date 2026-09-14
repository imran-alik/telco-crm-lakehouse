from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Alert:
    alert_type: str
    severity: str
    metric_value: float
    threshold: float
    message: str


def evaluate_thresholds(kpis: dict[str, Any]) -> list[Alert]:
    alerts: list[Alert] = []
    resolution = float(kpis.get("call_resolution_pct", 0))
    if resolution < 70.0:
        alerts.append(
            Alert(
                alert_type="LOW_CALL_RESOLUTION",
                severity="warning",
                metric_value=resolution,
                threshold=70.0,
                message="Call resolution below SLA threshold",
            )
        )
    conversion = float(kpis.get("offer_conversion_pct", 0))
    if conversion < 10.0:
        alerts.append(
            Alert(
                alert_type="LOW_OFFER_CONVERSION",
                severity="info",
                metric_value=conversion,
                threshold=10.0,
                message="Offer conversion below target",
            )
        )
    return alerts
