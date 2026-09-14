from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class DeadLetterQueue:
    def __init__(self, dlq_dir: str | Path) -> None:
        self.dlq_dir = Path(dlq_dir)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def route(self, source: str, raw_data: dict[str, Any], reason: str) -> Path:
        digest = hashlib.sha256(
            json.dumps(
                {"source": source, "raw": raw_data, "reason": reason}, sort_keys=True, default=str
            ).encode()
        ).hexdigest()[:12]
        filepath = self.dlq_dir / f"dlq_{source}_{digest}.json"
        if filepath.exists():
            return filepath
        payload = {
            "quarantined_at": datetime.now(UTC).isoformat(),
            "source": source,
            "failure_reason": reason,
            "raw_payload": raw_data,
        }
        filepath.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return filepath

    def count(self) -> int:
        return len(list(self.dlq_dir.glob("dlq_*.json")))
