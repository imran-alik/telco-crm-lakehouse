# Dependency Catalog & Libraries Maintenance — Telco CRM Lakehouse

This document catalogs the dependencies, external libraries, and standard library components utilized by the Telco CRM Medallion Lakehouse platform. It details their sources, licenses, pin strategies, and maintenance runbooks.

---

## 📦 1. Pip Dependencies Catalog

The platform utilizes a highly optimized set of core libraries, minimizing runtime footprints while securing structural schemas and transactional performance.

| Package Name | PyPI Sources | Official Documentation | Minimum Pin | License | Role in Platform |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **duckdb** | [PyPI Page](https://pypi.org/project/duckdb/) | [DuckDB Docs](https://duckdb.org/docs/) | `==1.1.0` | MIT | Embedded columnar SQL analytics engine. |
| **pydantic** | [PyPI Page](https://pypi.org/project/pydantic/) | [Pydantic Docs](https://docs.pydantic.dev/) | `==2.8.2` | MIT | Schema boundary validation and type enforcement. |
| **pytest** | [PyPI Page](https://pypi.org/project/pytest/) | [Pytest Docs](https://docs.pytest.org/) | `==9.1.1` | MIT | Behavioral, integration, and E2E unit testing. |
| **ruff** | [PyPI Page](https://pypi.org/project/ruff/) | [Ruff Docs](https://docs.astral.sh/ruff/) | `==0.16.7` | MIT | Developer linting and static code formatting. |

---

## 🏛️ 2. Standard Library Inventory

No untyped or third-party wrappers are utilized where standard library modules suffice. The system leverages:

- **`hashlib`**: For deterministic, cryptographically secure PII phone number (ANI) masking via SHA-256.
- **`re`**: For structural pattern matching used to obfuscate customer email domains.
- **`csv`**: For reading, streaming, and generating raw synthetically modeled records.
- **`pathlib`**: For platform-agnostic, absolute, and relative folder path evaluations (essential for Windows/Linux interoperability).
- **`dataclasses`**: For managing централизованные system configuration classes cleanly.
- **`shutil`**: For resetting sink folders and managing temporary folder workspaces.
- **`logging`**: For structured, level-based console instrumentation (replacing print statements).
- **`argparse`**: For accepting and parsing CLI options (e.g., executing specific medallion layers).

---

## 🛡️ 3. Upgrades, Audits, and Maintenance Runbook

### Runbook 1: Checking for Security Vulnerabilities
Data Engineers must execute audits monthly or before any major release.
```bash
# Verify virtual environment is active
source .venv/bin/activate

# Execute security scanning on dependencies
pip install pip-audit
pip-audit
```

### Runbook 2: Upgrading a Dependency
To upgrade a package (e.g. `pydantic`):
1. Create a developer branch: `git checkout -b feature/upgrade-pydantic`
2. Bump the version inside `codebase/requirements.txt` or `codebase/requirements-runtime.txt` (only for runtime dependencies).
3. Execute clean dependency install:
   ```bash
   pip install -r codebase/requirements.txt
   ```
4. Run the Pytest suite to ensure there are no breaking API mutations:
   ```bash
   python -m pytest
   ```
5. Trigger the E2E certification run to re-verify the quality gates:
   ```bash
   python codebase/scripts/certify_public_run.py
   ```
6. If all gates are green, record the upgrade details inside the [`CHANGELOG.md`](../CHANGELOG.md) file and merge the PR.

---

## 📊 4. Last Verified Environment Matrix

The system has been certified green and verified across the following environments:

| Component | Tested Version | Compatibility Range |
| :--- | :--- | :--- |
| **Python** | `3.12.10` | `3.12.x` - `3.13.x` |
| **OS Platform** | Windows 10 / 11 (PowerShell) | Win32 (x64) / Linux (Ubuntu) / macOS |
| **DuckDB** | `1.1.0` | `>=1.0.0` |
| **Pydantic** | `2.8.2` | `2.x.x` |
