# Design Commit — Pre-Merge Gate Checklist

> Run this checklist **before every merge-worthy commit or PR** on the telco CRM lakehouse pipeline repo.  
> Companion to [`data-engineering-design-standards.md`](./data-engineering-design-standards.md) and [`design-patterns.md`](./design-patterns.md).

**How to use:** Copy this checklist into your PR description. Every **Gate** must pass or be explicitly waived with reason in CHANGELOG.

---

## A. Branch & git hygiene

| # | Gate | Pass? | Notes |
|---|---|---|---|
| A1 | Branch created from latest `main` (not stale fork) | ☐ | `feature/*`, `docs/*`, `fix/*` |
| A2 | No secrets, `.env`, credentials, or tokens in diff | ☐ | Config via dataclass and env |
| A3 | `data/sink/`, `*.db`, `.pytest_cache/` not staged | ☐ | Runtime outputs gitignored |
| A4 | Commit message: imperative subject + **why** in body | ☐ | Link ask ID if behavior change |
| A5 | CHANGELOG.md updated under `[Unreleased]` or version | ☐ | Keep a Changelog format |

---

## B. Problem & narrative (does it make sense?)

| # | Gate | Pass? | Notes |
|---|---|---|---|
| B1 | README **Pipeline Outcomes** table with committed certification stats | ☐ | Matches latest `run_summary_*.json` |
| B2 | Tech stack + data model sections present | ☐ | design-patterns §1, §3 |
| B3 | Pipeline scripts linked (extract/transform/load/analytics) | ☐ | Module links |
| B4 | A reviewer finds verify steps in ≤2 clicks | ☐ | Getting started + certify command |
| B5 | Claims labeled: **Proven** vs **Documented** vs **Planned** | ☐ | Match DESIGN verdicts |
| B6 | No tutorial/BTS language in user-facing docs | ☐ | No “plug and play”, “simple”, “layman only” |
| B7 | Public data attribution present | ☐ | Synthetic Cisco/Genesis/Siebel reference |
| B8 | Production roadmap honest (not fake completeness) | ☐ | Databricks/Airflow/GCP as documented follow-ups |

---

## C. Design modularity & usability

| # | Gate | Pass? | Notes |
|---|---|---|---|
| C1 | Package folders match single-responsibility layout | ☐ | config/ schemas/ warehouse/ quality/ orchestration/ analytics/ |
| C2 | Orchestrator wires adapters; no 500-line god script | ☐ | `orchestration/pipeline.py` thin domain |
| C3 | Centralized config via dataclass / env | ☐ | central `settings.py` |
| C4 | CLI scripts are thin entrypoints | ☐ | `run_pipeline.py`, `certify_public_run.py` |
| C5 | New engineer can run certify + pytest without asking author | ☐ | HOW-TO-EXECUTE.md works copy-paste |

---

## D. Code ↔ doc ↔ file connectivity

| # | Gate | Pass? | Notes |
|---|---|---|---|
| D1 | `docs/CONNECTIVITY.md` maps every ask → module → test → doc section | ☐ | Traceability matrix complete |
| D2 | Every module in DESIGN §14 exists on disk | ☐ | No ghost paths |
| D3 | DESIGN schemas match Pydantic & database DDL | ☐ | Types and constraints align |
| D4 | SOLUTION.md ask IDs match DESIGN ask register | ☐ | A1…A8 consistent |
| D5 | README links resolve (DESIGN, SOLUTION, LIBRARIES) | ☐ | No broken relative links |

---

## E. Design document completeness

| # | Gate | Pass? | Notes |
|---|---|---|---|
| E1 | DESIGN.md has verdicts table with proof pointers | ☐ | |
| E2 | Source/sink schemas with idempotency keys | ☐ | |
| E3 | Lineage diagram + per-node failure behavior | ☐ | |
| E4 | Conn/disconnect matrix present | ☐ | |
| E5 | Data evolution section present | ☐ | Even if “v1 only” |
| E6 | Failure matrix + fallback section present | ☐ | DLQ, retry, checkpoint |
| E7 | Each ask has ASK → SOLUTION → CODE → OUTPUT | ☐ | In DESIGN §7 |
| E8 | Document control version row updated | ☐ | |

---

## F. Tests, lint, certification

| # | Gate | Pass? | Notes |
|---|---|---|---|
| F1 | `python -m pytest` → all green | ☐ | |
| F2 | `python codebase/scripts/certify_public_run.py` → exit 0 | ☐ | Certified public run passes |
| F3 | Ruff lint passes (if configured) | ☐ | Style and imports green |
| F4 | Idempotent replay test still passes | ☐ | Exactly-once validation |

---

## G. Evidence & quality gates

| # | Gate | Pass? | Notes |
|---|---|---|---|
| G1 | `data/evidence/run_summary_index.json` updated | ☐ | When certification re-run |
| G2 | Quality gates all `true` in latest evidence | ☐ | See certify script output |
| G3 | Row counts in evidence match README gate table | ☐ | Ingest totals align |
| G4 | Old failed evidence artifacts removed from commit | ☐ | No red runs committed |

---

## H. Libraries & dependency maintenance

| # | Gate | Pass? | Notes |
|---|---|---|---|
| H1 | `docs/LIBRARIES.md` exists with PyPI + docs link per pip package | ☐ | |
| H2 | `requirements-runtime.txt` contains only runtime deps | ☐ | duckdb, pydantic, etc. |
| H3 | Every line in `requirements*.txt` documented in LIBRARIES.md | ☐ | No orphan deps |

---

## I. Reviewer experience (final pass)

| # | Gate | Pass? | Notes |
|---|---|---|---|
| I1 | Clone → install → certify works on clean machine | ☐ | Python 3.12+ only dep |
| I2 | Architecture diagram renders in GitHub Markdown | ☐ | Mermaid valid |
| I3 | No placeholder TODO blocks in user-facing docs | ☐ | |
| I4 | SCALE-OUT / Databricks/Airflow notes clearly separated | ☐ | Local execution isolated |

---

## Quick pre-commit command block

```powershell
cd <repo-root>
# run validation:
$env:PYTHONPATH="codebase"
python -m pytest -q
python codebase/scripts/certify_public_run.py
```
