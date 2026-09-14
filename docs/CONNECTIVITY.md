# Traceability & Connectivity Matrix — Telco CRM Lakehouse

This document maps the connections of the platform, ensuring complete traceability across Requirements (Asks), Code Modules, Schemas, Test Classes, and Documentation sections.

---

## 🗺️ System Traceability Matrix

| Ask ID | Business / Technical Goal | Implementation Module | Schema / Data Structure | Test Scenario | Design Doc Section |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1** | Multi-source Ingestion & Schema Enforce | `orchestration/pipeline.py` (`_load_csv_to_bronze`) | `schemas/entities.py` (Pydantic models) | `test_pipeline.py` (`test_full_medallion_pipeline`) | `DESIGN.md` §6.1 / `SOLUTION.md` §A1 |
| **A2** | Quarantine & DLQ Routing | `quality/dlq.py` (`DeadLetterQueue`) | `quarantine_dlq/dlq_*.json` schema | `test_pipeline.py` (`test_full_medallion_pipeline`) | `DESIGN.md` §6.2 / `SOLUTION.md` §A2 |
| **A3** | Normalized 3NF Staging | `orchestration/pipeline.py` (`run_silver`) | `silver_customer`, `silver_agent` tables | `test_pipeline.py` (`test_full_medallion_pipeline`) | `DESIGN.md` §6.3 / `SOLUTION.md` §A3 |
| **A4** | Star Schema Dimensional Model | `orchestration/pipeline.py` (`run_gold`) | `gold_dim_*`, `gold_fact_*` tables | `test_pipeline.py` (`test_gold_star_tables_exist`) | `DESIGN.md` §6.4 / `SOLUTION.md` §A4 |
| **A5** | Centralized Configuration | `config/settings.py` (`LakehouseConfig`) | `@dataclass` parameters configuration | `test_pipeline.py` (temp path injection) | `DESIGN.md` §6.5 / `SOLUTION.md` §A5 |
| **A6** | Cryptographic Salts & Masking | `governance/masking.py` (`apply_legal_mask`) | SHA-256 with project salt & regex domains | `test_pipeline.py` (`test_legal_mask_hashes_ani`) | `DESIGN.md` §6.6 / `SOLUTION.md` §A6 |
| **A7** | Daily Campaign Finance Mart | `orchestration/pipeline.py` (`run_marts`) | `mart_finance_revenue` table schema | `test_pipeline.py` (`test_full_medallion_pipeline`) | `DESIGN.md` §6.7 / `SOLUTION.md` §A7 |
| **A8** | Predictive ML Feature Store | `orchestration/pipeline.py` (`run_marts`) | `mart_ml_features` table schema | `test_pipeline.py` (`test_full_medallion_pipeline`) | `DESIGN.md` §6.8 / `SOLUTION.md` §A8 |

---

## 📂 File-to-File Connectivity Diagram

Below is the directory relationship flow mapping how files in the repository depend on and relate to each other:

```
[config/settings.py]
       │ (provides paths & prefixes)
       ▼
[schemas/entities.py] ◄─── (validates raw records) ─── [data/source/samples/*.csv]
       │
       ▼ (ingests into DuckDB)
[orchestration/pipeline.py]
       │
       ├─► [quality/dlq.py] (writes invalid records here) ──► [data/sink/quarantine_dlq/*.json]
       │
       ├─► [governance/masking.py] (cryptographic SHA-256 masking) ──► [mart_legal_compliance]
       │
       ├─► [analytics/kpi.py] (computes call resolution & conversion)
       │
       ▼ (triggers E2E certification run)
[codebase/scripts/certify_public_run.py] ─── (generates) ───► [data/evidence/run_summary_*.json]
```

---

## 🧪 Documentation Reference Links

- **E2E Implementation Code Details**: [`SOLUTION.md`](../SOLUTION.md)
- **Authoritative System Design Details**: [`docs/DESIGN.md`](DESIGN.md)
- **Reviewer 5-Minute Handover Checklist**: [`docs/HANDOVER.md`](HANDOVER.md)
- **Databricks Unity Catalog & Airflow Blueprint**: [`docs/databricks/DATABRICKS-SERVICES.md`](docs/databricks/DATABRICKS-SERVICES.md)
