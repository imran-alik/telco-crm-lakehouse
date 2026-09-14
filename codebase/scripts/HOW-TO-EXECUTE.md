# Execution Runbook — Telco CRM Lakehouse

This runbook outlines the step-by-step instructions to set up, execute, and verify the Telco CRM Medallion pipeline.

---

## 📋 Prerequisites
- **Python 3.12+** must be installed and added to your system's PATH.
- No external databases are required—all operations run locally using an embedded DuckDB instance.

---

## ⚡ Step-by-Step Execution Guide

### Step 1: Set Up the Environment
Create and activate a clean Python virtual environment to isolate dependencies:
```bash
# Navigate to the repo folder
cd C:\Users\imran\Documents\Projects\telco-crm-lakehouse

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Linux / macOS)
source .venv/bin/activate
```

### Step 2: Install Required Libraries
Installs DuckDB, Pydantic, Pytest, and Ruff linter.
```bash
pip install -r codebase/requirements.txt
```

### Step 3: Configure Environment Variables
Set the python import path:
```bash
# Windows PowerShell
$env:PYTHONPATH="codebase"

# Linux / macOS
export PYTHONPATH="codebase"
```

### Step 4: Generate Reference Source Datasets
Executes the generator script, writing 4,440 highly-coupled mock transaction CSV logs representing CRM account profiles, ACD roster sheets, Cisco call detail records, demographics, NLP classification intent categories, and marketing campaign responses.
```bash
python codebase/scripts/generate_samples.py
```
*Verification*: Check that six `.csv` files have been written under `data/source/samples/`.

### Step 5: Execute the Medallion State Transitions
Triggers the full pipeline transition, loading the CSV files into Bronze tables, normalizing them into 3NF Silver tables, modeling the Gold dimensional Star Schema, and materializing three aggregate reporting Marts.
```bash
python codebase/scripts/run_pipeline.py --layer all
```
*Verification*: A single columnar database file `lakehouse.db` will be compiled inside `data/sink/`.

### Step 6: Certify the Platform Run (Quality Gate Check)
Runs the end-to-end certification script to assert schema structures, verify active quality gates, run a replay stability/idempotency test (ensuring exactly-once processing with zero duplicate logs), and write the run metadata JSON.
```bash
python codebase/scripts/certify_public_run.py
```
*Expected Outcome*: Command completes with exit code `0`, reporting that all quality gates passed. A unique `run_summary_telco_full_sample_*.json` is created in `data/evidence/` and appended to the local metadata index.

---

## 🧪 Step 7: Pytest behavioral Tests & Linting
Ensure codebase changes do not violate behavioral contracts:
```bash
# Verify code formatting and PEP-8 compliance
ruff check codebase tests

# Run all pytest assertions (unit, integration, and E2E)
python -m pytest tests/ -v
```
*Expected Outcome*: 5 tests collect and pass successfully, confirming hashing determinism, PII masking coverage, medallion table load structures, and star schema relationships.
