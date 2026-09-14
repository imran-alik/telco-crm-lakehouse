from __future__ import annotations

import hashlib
import re
from typing import Any


def hash_pii(value: str | None, *, salt: str = "telco_portfolio") -> str | None:
    if value is None or value == "":
        return None
    digest = hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:16]
    return f"HASH_{digest}"


def mask_email_domain(email_domain: str | None) -> str | None:
    if not email_domain:
        return None
    return re.sub(r"[a-zA-Z0-9]", "x", email_domain.split(".")[0]) + ".masked"


def apply_legal_mask(row: dict[str, Any]) -> dict[str, Any]:
    """Legal mart policy: no raw ANI, masked email domain, age band only."""
    masked = dict(row)
    if "ani_hash" in masked:
        masked["ani_hash"] = hash_pii(str(masked.get("ani_hash")))
    if "email_domain" in masked:
        masked["email_domain"] = mask_email_domain(str(masked.get("email_domain")))
    return masked
