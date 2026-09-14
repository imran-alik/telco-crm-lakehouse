# Databricks / Production Mapping

| Local | Production | Notes |
|---|---|---|
| bronze_* tables | Delta bronze in Unity Catalog | Auto Loader from ADLS landing |
| silver_* | Delta silver (3NF) | DLT expectations + quarantine |
| gold_dim/fact | Delta gold star | MERGE on surrogate keys |
| mart_* | UC governed schemas | finance / legal / ml schemas |
| masking.py | UC column masks + row filters | legal consumer RBAC |
| certify_public_run.py | Databricks job + metrics table | quality gates as task values |
| docker-compose scheduler | Airflow / Databricks Workflows | bronze→silver→gold→marts DAG |
| GitHub Actions CI | Repo CI + Databricks Asset Bundles deploy | lint/test before bundle publish |

Release cycle target: CI/CD reduces manual release from ~2 days to ~4 hours via automated lint, test, and packaging gates.
