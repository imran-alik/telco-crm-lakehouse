from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDALLION_ROOT = REPO_ROOT / "medallion"


def load_layer_sql(layer: str, filename: str, **prefixes: str) -> str:
    path = MEDALLION_ROOT / layer / "sql" / filename
    template = path.read_text(encoding="utf-8")
    return template.format(**prefixes)


def load_layer_sql_batch(layer: str, filenames: list[str], **prefixes: str) -> list[str]:
    return [load_layer_sql(layer, name, **prefixes) for name in filenames]
