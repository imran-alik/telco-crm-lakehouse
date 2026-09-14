# How to Execute

## Local (recommended first)

1. Install Python 3.12+
2. `py -3.12 -m pip install -r codebase/requirements.txt`
3. `$env:PYTHONPATH="codebase"`
4. `py -3.12 codebase/scripts/certify_public_run.py` → exit **0**
5. `py -3.12 -m pytest -q` → **6 passed**

## Docker

```powershell
docker compose build
docker compose run --rm pipeline
docker compose up scheduler
```

Scheduler runs bronze → silver → gold → marts via `scheduler/run_layers.sh`.

## CI parity

```powershell
.\codebase\scripts\bootstrap.ps1
```

Matches GitHub Actions: design-commit → ruff → pytest → certify.
