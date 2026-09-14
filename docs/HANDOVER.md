# Handover — Telco CRM Lakehouse

## Verify in 5 minutes

```powershell
cd telco-crm-lakehouse
py -3.12 -m pip install -r codebase\requirements.txt
$env:PYTHONPATH="codebase"
py -3.12 codebase\scripts\certify_public_run.py
py -3.12 -m pytest -q
```

| Pass criteria | Expected |
|---|---|
| Certify exit code | `0` |
| Bronze rows | 4440 |
| DLQ | 0 |
| pytest | 6 / 6 |

## Docker verify

```powershell
docker compose build
docker compose run --rm pipeline
```

## Key modules

| Concern | Path |
|---|---|
| Config | `codebase/telco_lakehouse/config/settings.py` |
| Pipeline | `codebase/telco_lakehouse/orchestration/pipeline.py` |
| Masking | `codebase/telco_lakehouse/governance/masking.py` |
| Samples | `codebase/scripts/generate_samples.py` |
| CI | `.github/workflows/ci.yml` |

## Production mapping

See [databricks/DATABRICKS-SERVICES.md](databricks/DATABRICKS-SERVICES.md).
