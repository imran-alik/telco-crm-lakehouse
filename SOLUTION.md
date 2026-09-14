# SOLUTION — Telco CRM Lakehouse

## A1 — Ingest multi-source CSVs to bronze

**Code:** `codebase/telco_lakehouse/orchestration/pipeline.py` → `run_bronze()`  
**Expected output:** 4440 rows across 6 bronze tables, 0 DLQ on committed sample.

## A2 — Validate + DLQ

**Code:** `codebase/telco_lakehouse/schemas/*`, `quality/dlq.py`  
**Expected output:** Invalid rows quarantined under `data/sink/quarantine_dlq/`.

## A3 — Silver 3NF

**Code:** `run_silver()`  
**Expected output:** 4140 silver rows (entity-normalized).

## A4 — Gold star schema

**Code:** `run_gold()`  
**Expected output:** 8 gold tables, 1500 `gold_fact_call` rows.

## A5 — Finance mart

**Code:** `run_marts()` → `mart_finance_revenue`  
**Expected output:** Revenue by date × segment × campaign; conversion_pct column.

## A6 — Legal mart (masked)

**Code:** `governance/masking.py` + `mart_legal_compliance`  
**Expected output:** 1500 rows, ANI hashed, no raw CLI.

## A7 — ML feature mart

**Code:** `mart_ml_features`  
**Expected output:** 300 customer-level feature rows.

## A8 — KPIs + alerts

**Code:** `analytics/kpi.py`  
**Expected output:** call_resolution_pct, offer_conversion_pct, revenue; LOW_CALL_RESOLUTION alert when < 70%.
