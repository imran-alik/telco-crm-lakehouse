# Local verification harness — lint, tests, certification (Windows PowerShell)
# Usage from repo root:  .\codebase\scripts\bootstrap.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

Write-Host "==> Repo root: $Root"

$Python = "py -3.12"
if ($env:VIRTUAL_ENV) {
    $Python = "python"
    Write-Host "==> Using active venv: $env:VIRTUAL_ENV"
} elseif (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python 3.12+ from https://www.python.org/downloads/"
}

Write-Host "==> Installing runtime + dev dependencies..."
Invoke-Expression "$Python -m pip install --upgrade pip"
Invoke-Expression "$Python -m pip install -r codebase\requirements.txt ruff pytest"

$env:PYTHONPATH = "codebase"

Write-Host "==> Generate samples (if missing)..."
if (-not (Test-Path "data\source\samples\calls.csv")) {
    Invoke-Expression "$Python codebase\scripts\generate_samples.py"
}

Write-Host "==> Design-commit static checks..."
Invoke-Expression "$Python codebase\scripts\check_design_commit.py"

Write-Host "==> Lint..."
Invoke-Expression "$Python -m ruff check codebase tests"

Write-Host "==> Tests..."
Invoke-Expression "$Python -m pytest -q"

Write-Host "==> Telco sample certification (offline)..."
Invoke-Expression "$Python codebase\scripts\certify_public_run.py"

Write-Host ""
Write-Host "VERIFICATION OK — tests and certification passed on committed sample."
