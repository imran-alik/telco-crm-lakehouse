# Data Engineering Design Patterns — Telco CRM Lakehouse

> Portfolio and pipeline patterns distilled from production-oriented repos — not tutorial walkthroughs.  
> Reference implementations: [vishal-bulbule](https://github.com/vishal-bulbule) (GCP DE projects), [uber-data-engineering-mage-project](https://github.com/darshilparmar/uber-data-engineering-mage-project) (ETL + analytics SQL), [Retail_Analysis_Redshift](https://github.com/ansamAY/Retail_Analysis_Redshift) (layered warehouse models).

Use with [`data-engineering-design-standards.md`](./data-engineering-design-standards.md) and [`design-commit.md`](./design-commit.md).

---

## 1. Portfolio README pattern (GitHub front door)

A hiring reviewer spends **≤60 seconds** on the repo landing page. Structure like a featured project on an engineer profile — not a course syllabus.

### 1.1 Required above-the-fold content

| Block | Pattern source | What to show |
|---|---|---|
| **Title + domain** | [vishal-bulbule featured projects](https://github.com/vishal-bulbule) | `{Domain} \| {Pattern} on {Cloud}` — e.g. *Telco CRM Medallion Lakehouse \| Data Pipeline on Databricks* |
| **Tech stack table** | [Retail_Analysis_Redshift](https://github.com/ansamAY/Retail_Analysis_Redshift) | Layer × tool × production analogue |
| **Pipeline outcomes** | This repo's certification JSON | **Committed stats** — row counts, call resolution, offer conversion, total revenue, DLQ rate, replay stability |
| **Architecture** | [uber-data-engineering-mage-project](https://github.com/darshilparmar/uber-data-engineering-mage-project) | Diagram (Mermaid) with **module paths**, not generic boxes |
| **Data model overview** | Retail `dim_` / `fact_` / marts | Medallion layers (Bronze/Silver/Gold/Marts) with grain and keys |
| **Pipeline scripts** | Uber extract/load/transform links | Direct links to ingestion, orchestration, warehouse, analytics modules |
| **Getting started** | Retail numbered steps | Install → certify → test — with **pass criteria**, not marketing copy |
| **Design docs** | Internal standard | Links to `DESIGN.md`, `SOLUTION.md`, `HANDOVER.md` |

### 1.2 Language — engineer vs tutorial (BTS)

| Avoid (tutorial / BTS tone) | Use (engineer tone) |
|---|---|
| plug and play | reproducible certification harness |
| simple / easy | local emulator of `{production service}` |
| just run / we'll leverage | execute / implements |
| layman view / plain language only | business context + measurable outcomes |
| dive into the world of | processes / ingests / emits |
| toy demo | local proof with committed evidence |
| magic / automatically handles | deterministic UPSERT on `{key}` |

Commits and CHANGELOG entries follow the same rule: **imperative subject + measurable outcome in body**.

---

## 2. Medallion Layer Separation

Separate concerns into named pipeline stages with **one module/class per stage**:

| Stage | Responsibility | Local Module / Action | Databricks / Production analogue |
|---|---|---|---|
| **Bronze** | Ingest CSVs, enforce Pydantic types, write DLQ | `TelcoLakehousePipeline.run_bronze()` | Spark Structured Streaming / Auto Loader |
| **Silver** | Cleanse, denormalize, staging 3NF tables | `TelcoLakehousePipeline.run_silver()` | Delta Lake Silver tables (merge / SCD Type 1) |
| **Gold** | Build star schema dimension & fact tables | `TelcoLakehousePipeline.run_gold()` | Unity Catalog Gold tables / dbt core |
| **Marts** | Create consumer reporting & analytical marts | `TelcoLakehousePipeline.run_marts()` | BI layers / Feature Store / dbt marts |
| **Certify** | Observability, KPI verification, evidence generation | `codebase/scripts/certify_public_run.py` | Great Expectations / dbt test |

Orchestrator wires adapters; **business rules stay in orchestrator**, I/O in stage modules.

---

## 3. Layered data model (Retail / dbt pattern)

Name layers by **warehouse convention**, even when local:

| Layer | Prefix / name | Grain | Idempotency key |
|---|---|---|---|
| **Source** | CSV files | 1 row = 1 interaction | Pydantic validation checks |
| **Bronze** | `bronze_*` | 1 row = 1 validated record | table recreate / insert |
| **Silver** | `silver_*` | 1 row = 1 normalized entity | table recreate / select |
| **Gold** | `gold_dim_*`, `gold_fact_*` | 1 row = 1 dimension/fact | dimensional keys |
| **Marts** | `mart_*` | reporting & analytical aggregates | segment, campaign, and customer keys |
| **DLQ** | `quarantine_dlq/*.json` | 1 file = 1 poison record | payload hash |

Document the model in README **before** folder tree. Reviewers care about grain and keys first.

---

## 4. Evidence-driven outcomes (production proof pattern)

Every portfolio pipeline must answer: **what changed in the data after this run?**

### 4.1 Committed outcome artifact

Certification writes JSON with:

- `pipeline.bronze`, `pipeline.silver`, `pipeline.gold`, `pipeline.marts` row counts.
- `quality_gates` booleans (all must be `true` to commit).
- `replay` block proving idempotency (same row count, zero duplicate records).

Index file `data/evidence/run_summary_index.json` points to latest artifact.

### 4.2 README outcome table (mandatory)

Surface **net activity outcome** on README — not buried in `data/evidence/`.

---

## 5. Security & Masking Patterns

| Pattern | Implementation | Proves |
|---|---|---|
| **Cryptographic Hashing** | SHA-256 with project salt | Caller PII (ANI) anonymization for GDPR/CCPA |
| **Email Domain Masking** | Regex character replacement | Structural domain masking (e.g. `example.com` → `xxxxxxx.masked`) |
| **Column Separation** | Restrict tables at Mart level | Role-based data access (Compliance vs Analytics) |

---

## 6. Quality and resilience patterns

| Pattern | When | Module |
|---|---|---|
| **Schema validation** | Boundary ingest | `schemas/` (Pydantic) |
| **DLQ quarantine** | Row-level validation failure | `quality/dlq.py` |
| **Deduplication** | Distinct selects | `orchestration/pipeline.py` |
| **Idempotent replay** | Isolate and reset DB | `scripts/certify_public_run.py` |

Label each pattern **Proven (local)** vs **Documented (scale-out)** in DESIGN verdicts.

---

## 7. Commit message pattern

```
feat(ingestion): add pydantic schema validation for CDR calls

Synthetic samples certification still passes 1500/1500 calls with idempotent replay.
Evidence index updated — quality gates green.

Refs: A1, A2
```
