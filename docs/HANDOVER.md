# Handover Document — Telco CRM Medallion Lakehouse

> A 5-minute platform verify runbook and operational checklist for incoming engineers.

---

## ⚡ 5-Minute Verification Runbook

To confirm the platform's integrity on a clean setup, execute the following commands in order:

```bash
# 1. Activate your virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Run the Behavioral Test Suite
python -m pytest tests/ -v

# 3. Execute the E2E Medallion Pipeline and Observation Gate
python codebase/scripts/certify_public_run.py
```

### ✅ Pass Criteria & Proof Points
* **Pytest Exit Code**: `0` (asserting all 5 test scenarios pass).
* **Certification Exit Code**: `0` (asserting all 10 quality gates pass).
* **Database State**: A single DuckDB file is written to `data/sink/lakehouse.db` with populated tables.
* **Evidence Output**: A unique signed JSON is added to `data/evidence/` (e.g. `run_summary_telco_full_sample_*.json`) and added to the registry metadata inside `data/evidence/run_summary_index.json`.

---

## 🛠️ Datastore & Warehouse Inspections

You can verify and query database tables using standard DuckDB CLI, Python, or standard SQL editors.

### Querying via Python
```python
import duckdb

# Connect to the local DuckDB warehouse
conn = duckdb.connect("data/sink/lakehouse.db", read_only=True)

# 1. Verify Mart Counts
print(conn.execute("SELECT COUNT(*) FROM mart_finance_revenue").fetchone())

# 2. Inspect Salted SHA-256 Masking on Legal Compliance Mart
print(
    conn.execute(
        "SELECT call_id, ani_hash, email_domain FROM mart_legal_compliance LIMIT 3"
    ).fetchdf()
)

conn.close()
```

---

## 📂 Operational Checklist & Maintenance Tasks

### Task 1: Adding a New Ingestion Schema (Bronze)
1. Add the raw source model as a Pydantic boundary class in `codebase/telco_lakehouse/schemas/entities.py`.
2. Register the table name and Pydantic model mapping inside `SAMPLE_FILES` in `codebase/telco_lakehouse/orchestration/pipeline.py`.
3. Update `codebase/scripts/generate_samples.py` to support synthetic data generation for the new dataset.
4. Rerun `python codebase/scripts/certify_public_run.py` to verify the quality gates pass.

### Task 2: Modifying Masking and Governance Rules
1. Core security functions reside inside `codebase/telco_lakehouse/governance/masking.py`.
2. To rotate the cryptographic hashing salt, update the keyword-only parameter `salt` inside `hash_pii`.
3. When rules are altered, ensure you update the pytest assertions inside `tests/test_pipeline.py` and execute `python -m pytest`.

### Task 3: Troubleshooting Schema Failures (DLQ Inspections)
If a source record fails ingestion boundary validation, the row is routed to `data/sink/quarantine_dlq/` as a JSON file.
- **Inspect**: Open the quarantine file. It contains the exact `quarantined_at` timestamp, `source` CSV name, `failure_reason` (Pydantic validation trace), and the unmodified `raw_payload`.
- **Resolution**: Patch the upstream system generating the CSV file, or evolve the Pydantic type validator inside the codebase if the drift is an approved schema evolution.

---

## 📈 Platform Handoff Contacts

- **Lead Systems Architect**: Imran Ali Khan
- **Primary Repo Target**: `C:\Users\imran\Documents\Projects\telco-crm-lakehouse`
- **Documentation Core**: [`README.md`](../README.md) · [`DESIGN.md`](./DESIGN.md) · [`SOLUTION.md`](../SOLUTION.md)
