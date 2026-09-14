from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_certification_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "codebase" / "scripts" / "certify_public_run.py")],
        cwd=ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "codebase")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    index = json.loads(
        (ROOT / "data" / "evidence" / "run_summary_index.json").read_text(encoding="utf-8")
    )
    assert index["runs"]
