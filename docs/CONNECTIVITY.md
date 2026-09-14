# Connectivity Matrix

| Component | Connects to | Protocol | Disconnect / fallback |
|---|---|---|---|
| Bronze loader | Local CSV samples | file I/O | DLQ on validation failure |
| DuckDB warehouse | `data/sink/lakehouse.db` | embedded SQL | checkpoint on close |
| Finance mart | gold facts + bronze offers | SQL JOIN | empty mart if no offers |
| Legal mart | bronze calls + masking | Python + SQL | hash fallback for ANI |
| ML mart | CRM + calls + intent | SQL aggregation | NULL features for orphans |
| Evidence writer | `data/evidence/` | JSON files | index append-only |
| Docker pipeline | certify script | container CMD | non-zero exit fails CI |
| Scheduler | run_layers.sh | shell loop | exit-on-fail per layer |
| GitHub Actions | pytest + ruff | CI runner | fail PR on red |
