# Databricks & Airflow Scaling Blueprint — Telco CRM Lakehouse

This document details the scale-out mapping required to migrate the single-node local DuckDB pipeline to an enterprise-grade cloud architecture utilizing **Databricks Unity Catalog**, **Delta Lake**, and **Apache Airflow**.

---

## 🗺️ 1. Local to Cloud Architecture Mapping

The local system design is intentionally structured around the medallion framework to enable direct translation to cloud components:

```
[Local Environment (Single-Node)]              [Production Databricks Environment (Scale-Out)]
   CSV Data Streams in Local Files ──────────────► Auto Loader on GCS/ADLS Raw Buckets
         Pydantic v2 Ingestion ──────────────────► PySpark Structured Streaming (Schema Evolution)
            DuckDB Bronze Table ─────────────────► Delta Lake Bronze Table (Append-Only)
            DuckDB Silver Table ─────────────────► Delta Lake Silver Table (MERGE / SCD Type 1)
            DuckDB Gold Tables ──────────────────► Unity Catalog Gold Dimension & Fact Tables
        Custom Python Cryptography ──────────────► Unity Catalog Dynamic Column Masking Policies
        Python CLI Subprocess Runner ────────────► Apache Airflow DAG Orchestration
```

---

## 📁 2. Databricks Medallion Layer Implementation

### Bronze Layer (Ingestion & Auto Loader)
In production, CSV files landing in GCS/ADLS raw zones are ingested stream-by-stream using Databricks **Auto Loader**.
- **Fidelity Check**: Auto Loader automatically infers raw column structures, capturing schema drifts and placing corrupted records inside a managed `_rescued_data` column (production dead-letter queue analogue).
- **Format**: Managed Delta Lake tables.

```python
# Production PySpark Auto Loader Ingest Template
df = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation", "dbfs:/schemas/bronze_calls")
    .option("header", "true")
    .load("gs://telecom-raw-zone/calls/")
)

(
    df.writeStream.format("delta")
    .option("checkpointLocation", "dbfs:/checkpoints/bronze_calls")
    .table("unity_catalog.telco_bronze.calls")
)
```

### Silver Layer (Staging & Delta MERGE)
The Silver layer staging structures are loaded incrementally. Since source updates can occur, PySpark `MERGE INTO` SQL commands are executed to upsert metrics deterministically based on operational business keys (e.g. `call_id`, `customer_id`).

```sql
-- Production Delta Merge Staging Template
MERGE INTO unity_catalog.telco_silver.customer AS target
USING (
  SELECT c.customer_id, c.account_num, c.party_type, c.segment, c.tenure_months, c.status, c.email_domain,
         d.region, d.age_band, d.plan_tier
  FROM unity_catalog.telco_bronze.customers_crm c
  LEFT JOIN unity_catalog.telco_bronze.demographics d ON c.customer_id = d.customer_id
) AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN
  UPDATE SET target.status = source.status, target.plan_tier = source.plan_tier
WHEN NOT MATCHED THEN
  INSERT *;
```

### Gold Layer (Dimensional Optimization)
Gold tables are mapped as Unity Catalog managed dimension and fact tables, utilizing **Liquid Clustering** or **Z-ORDER** on joining keys to guarantee fast BI aggregates:

```sql
-- Gold Fact Clustering Optimization
ALTER TABLE unity_catalog.telco_gold.fact_call CLUSTER BY (customer_key, date_key);
```

---

## 🛡️ 3. Unity Catalog Security & Governance Policies

Rather than executing custom Python-native cryptographic hashing during ETL runtime (as done locally in `governance/masking.py`), production environments leverage Databricks **Unity Catalog dynamic masking policies**.

This separates security rules from physical data tables, applying masking at **query execution time** depending on the viewing user's role (e.g. legal auditors can view unmasked ANIs, whereas marketing analysts see hashed identifiers).

```sql
-- Production Dynamic ANI (Phone ID) Masking Policy
CREATE MASK POLICY unity_catalog.governance.ani_mask AS (
  (val STRING) -> CASE 
    WHEN is_member('legal_auditor_role') THEN val
    ELSE sha2(concat('telco_portfolio_salt', val), 256)
  END
);

-- Apply Masking Policy on the call Fact Table
ALTER TABLE unity_catalog.telco_gold.fact_call 
ALTER COLUMN ani_hash SET MASK unity_catalog.governance.ani_mask;
```

---

## 🌀 4. Apache Airflow DAG Orchestration

The Python CLI runner `certify_public_run.py` is scale-mapped to an Apache Airflow DAG. Airflow schedules, triggers, and monitors medallion transitions across Databricks SQL Warehouses or job clusters.

```python
# Production Airflow DAG Template
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "imran_ali_khan",
    "depends_on_past": False,
    "start_date": datetime(2026, 9, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "telco_medallion_lakehouse",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:
    # 1. Trigger Auto Loader stream ingestion
    ingest_bronze = DatabricksSubmitRunOperator(
        task_id="ingest_bronze",
        json={"notebook_task": {"notebook_path": "/Notebooks/Ingest_Bronze"}},
    )

    # 2. Trigger Silver Normalization and Cleansing
    build_silver = DatabricksSubmitRunOperator(
        task_id="build_silver", json={"notebook_task": {"notebook_path": "/Notebooks/Build_Silver"}}
    )

    # 3. Trigger Gold Star Modeling
    build_gold = DatabricksSubmitRunOperator(
        task_id="build_gold", json={"notebook_task": {"notebook_path": "/Notebooks/Build_Gold"}}
    )

    # 4. Refresh Consumer Analytical Marts
    refresh_marts = DatabricksSubmitRunOperator(
        task_id="refresh_marts",
        json={"notebook_task": {"notebook_path": "/Notebooks/Refresh_Marts"}},
    )

    # Linear Medallion Dependencies
    ingest_bronze >> build_silver >> build_gold >> refresh_marts
```
