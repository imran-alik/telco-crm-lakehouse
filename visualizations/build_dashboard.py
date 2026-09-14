#!/usr/bin/env python
"""Build interactive HTML dashboard from latest certified run evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "evidence"
OUT_HTML = EVIDENCE / "dashboard.html"
OUT_JSON = EVIDENCE / "dashboard_metrics.json"


def _latest_run() -> dict:
    index_path = EVIDENCE / "run_summary_index.json"
    if not index_path.exists():
        raise FileNotFoundError("run_summary_index.json missing — run certify_public_run.py first")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    latest = index["runs"][-1]["artifact"]
    artifact_path = Path(latest)
    if not artifact_path.is_absolute():
        artifact_path = EVIDENCE / artifact_path.name
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def _render_html(payload: dict) -> str:
    kpis = payload.get("kpis", {})
    gates = payload.get("quality_gates", {})
    passed = sum(1 for v in gates.values() if v)
    total = len(gates)
    resolution = kpis.get("call_resolution_pct", 0)
    conversion = kpis.get("offer_conversion_pct", 0)
    revenue = kpis.get("total_offer_revenue_usd", 0)
    bronze = payload.get("pipeline", {}).get("layer_counts", {}).get("bronze_total", 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Telco Lakehouse — Certified Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .sub {{ color: #94a3b8; margin-bottom: 1.5rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
    .card {{ background: #1e293b; padding: 1rem; border-radius: 8px; }}
    .card b {{ display: block; font-size: 1.5rem; color: #38bdf8; }}
    #chart {{ margin-top: 2rem; background: #1e293b; border-radius: 8px; padding: 1rem; }}
    .gate {{ color: #4ade80; }}
  </style>
</head>
<body>
  <h1>Telco CRM Lakehouse</h1>
  <p class="sub">Redacted portfolio design · synthetic samples · certified run evidence</p>
  <div class="cards">
    <div class="card">Bronze rows<b>{bronze}</b></div>
    <div class="card">Call resolution<b>{resolution}%</b></div>
    <div class="card">Offer conversion<b>{conversion}%</b></div>
    <div class="card">Offer revenue<b>${revenue:,.2f}</b></div>
    <div class="card">Quality gates<b class="gate">{passed}/{total}</b></div>
  </div>
  <div id="chart"></div>
  <script>
    Plotly.newPlot('chart', [{{
      type: 'bar',
      x: ['Resolution %', 'Conversion %', 'Revenue (k USD)'],
      y: [{resolution}, {conversion}, {revenue / 1000.0}],
      marker: {{ color: ['#38bdf8', '#a78bfa', '#4ade80'] }}
    }}], {{
      paper_bgcolor: '#1e293b',
      plot_bgcolor: '#1e293b',
      font: {{ color: '#e2e8f0' }},
      title: 'Certified KPI Snapshot'
    }}, {{ responsive: true }});
  </script>
</body>
</html>"""


def main() -> int:
    payload = _latest_run()
    metrics = {
        "kpis": payload.get("kpis", {}),
        "quality_gates": payload.get("quality_gates", {}),
        "layer_counts": payload.get("pipeline", {}).get("layer_counts", {}),
    }
    OUT_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    OUT_HTML.write_text(_render_html(payload), encoding="utf-8")
    print(json.dumps({"dashboard_html": str(OUT_HTML), "metrics_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
