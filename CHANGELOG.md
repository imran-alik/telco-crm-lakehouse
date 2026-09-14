# Changelog — Telco CRM Lakehouse

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-14

### Added
- Created complete documentation portfolio matching SDE standards.
- Designed and authored [`README.md`](README.md) featuring vishal-bulbule style headers, certified outcome metrics, Databricks-Airflow scaling pathways, and directories.
- Authored comprehensive [`docs/DESIGN.md`](docs/DESIGN.md) system design detailing verdicts, full schemas, lineage failure parameters, data evolution, and ask register mapping (A1-A8).
- Designed [`docs/HANDOVER.md`](docs/HANDOVER.md) outlining 5-minute verification runbooks, database query inspection guidelines, and operational tasks.
- Created [`docs/CONNECTIVITY.md`](docs/CONNECTIVITY.md) defining a system-wide traceability matrix mapping requirements to files, modules, and tests.
- Designed [`docs/LIBRARIES.md`](docs/LIBRARIES.md) logging runtime and developer package details, PyPI upstream URLs, standard library usage, and library audit runbooks.
- Developed [`docs/databricks/DATABRICKS-SERVICES.md`](docs/databricks/DATABRICKS-SERVICES.md) scale-out blueprint mapping local modules to Databricks Auto Loader, Delta Lake, Unity Catalog governance, and Airflow DAGs.
- Created sanitized design standard files inside `docs/standards/` (`data-engineering-design-standards.md`, `design-commit.md`, `design-patterns.md`).
- Written [`SOLUTION.md`](SOLUTION.md) mapping each ask (A1-A8) to architectural decisions, codebase SQL/Python APIs, and expected output counts.
- Created [`commands.txt`](commands.txt) logging copy-pasteable execution and validation console commands.
- Authored [`analytics_query.sql`](analytics_query.sql) providing standalone analytical reporting templates on DuckDB Bronze tables.
- Created [`codebase/scripts/HOW-TO-EXECUTE.md`](codebase/scripts/HOW-TO-EXECUTE.md) outlining clear execution steps.

### Fixed
- Patched DuckDB SQL Type Binder exception in `run_marts` inside `codebase/telco_lakehouse/orchestration/pipeline.py` by applying strict `CAST(... AS DOUBLE)` on dynamically loaded string values inside CASE statements.
- Cleared Python standard compilation `__pycache__` conflicts inside `telco-crm-lakehouse/` to force recompilation of clean `.py` source.

---

## [1.0.0] - 2026-09-14

### Added
- Initial baseline commit adding telco CRM medallion lakehouse core algorithms.
- Configured schema validators, DLQ quarantine, cryptographic masking logic, and DuckDB medallion loaders.
- Configured synthetic sample generators and Pytest behavioural test files.
