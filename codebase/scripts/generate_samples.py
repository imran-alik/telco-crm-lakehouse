#!/usr/bin/env python
"""Generate committed telco CRM / contact-center sample CSVs."""

from __future__ import annotations

import csv
import hashlib
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from telco_lakehouse.config.settings import SampleGenerationConfig
from telco_lakehouse.schemas import (
    AgentRecord,
    CallCdrRecord,
    CustomerCrmRecord,
    DemographicsRecord,
    IntentLabelRecord,
    OfferDispositionRecord,
)

PARTY_TYPES = ["Individual", "Organization"]
SEGMENTS = ["Consumer", "SMB", "Enterprise"]
CUSTOMER_STATUSES = ["Active", "Active", "Active", "Suspended", "Closed"]
EMAIL_DOMAINS = ["example.com", "mail.test", "inbox.demo", "contact.sample"]

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery",
    "Blake", "Cameron", "Drew", "Emery", "Finley", "Harper", "Jamie", "Kendall",
]
LAST_NAMES = [
    "Nguyen", "Patel", "Garcia", "Kim", "Chen", "Williams", "Brown", "Davis",
    "Martinez", "Robinson", "Clark", "Lewis", "Walker", "Hall", "Young", "King",
]

TEAMS = ["Sales", "Retention", "Support", "Billing"]
SKILL_GROUPS = ["Spanish", "Technical", "Premium", "General"]
SITES = ["SITE-NYC", "SITE-CHI", "SITE-DAL", "SITE-ATL", "SITE-PHX"]

CHANNELS = ["voice", "voice", "voice", "chat", "callback"]
QUEUES = ["SALES-Q", "SUPPORT-Q", "RETENTION-Q", "BILLING-Q", "TECH-Q"]
DISPOSITIONS = ["ANSWERED", "ANSWERED", "ANSWERED", "ABANDONED", "TRANSFER", "VOICEMAIL", "CALLBACK_SCHEDULED"]
DNIS_NUMBERS = ["18005551234", "18005555678", "18885550100", "18885550200"]

CAMPAIGNS = ["RETENTION_2026", "UPSELL_FIBER", "ADD_LINE_Q3", "LOYALTY_RENEW", "PREMIUM_UPGRADE"]
OFFER_IDS = ["OFR-001", "OFR-002", "OFR-003", "OFR-004", "OFR-005"]
OFFER_RESPONSES = ["Accepted", "Declined", "No Response"]

INTENT_CATEGORIES = [
    "billing", "technical", "cancel", "upgrade", "account_change", "outage", "general_inquiry",
]

REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
PLAN_TIERS = ["Basic", "Plus", "Premium", "Fiber"]


def _ani_hash(customer_index: int, call_index: int) -> str:
    synthetic_ani = f"+1555{1000000 + customer_index * 17 + call_index:07d}"
    return hashlib.sha256(synthetic_ani.encode("utf-8")).hexdigest()


def build_customers(cfg: SampleGenerationConfig) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(cfg.customers_count):
        record = CustomerCrmRecord(
            customer_id=f"CUST-{i + 1:05d}",
            account_num=f"ACC-{10000000 + i}",
            party_type=PARTY_TYPES[i % len(PARTY_TYPES)],
            segment=SEGMENTS[i % len(SEGMENTS)],
            tenure_months=(i * 3 + 7) % 241,
            status=CUSTOMER_STATUSES[i % len(CUSTOMER_STATUSES)],
            email_domain=EMAIL_DOMAINS[i % len(EMAIL_DOMAINS)],
        )
        rows.append(record.model_dump())
    return rows


def build_agents(cfg: SampleGenerationConfig) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_hire = datetime(2018, 1, 15, tzinfo=UTC).date()
    for i in range(cfg.agents_count):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 3) % len(LAST_NAMES)]
        record = AgentRecord(
            agent_id=f"AGT-{i + 1:04d}",
            agent_name=f"{first} {last}",
            team=TEAMS[i % len(TEAMS)],
            skill_group=SKILL_GROUPS[i % len(SKILL_GROUPS)],
            site_id=SITES[i % len(SITES)],
            hire_date=base_hire + timedelta(days=i * 47),
        )
        rows.append(record.model_dump(mode="json"))
    return rows


def build_calls(cfg: SampleGenerationConfig, customer_ids: list[str], agent_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_start = datetime(2026, 8, 1, 8, 0, 0, tzinfo=UTC)
    for i in range(cfg.calls_count):
        customer_idx = i % len(customer_ids)
        disposition = DISPOSITIONS[i % len(DISPOSITIONS)]
        agent_id = None if disposition in {"ABANDONED", "VOICEMAIL"} else agent_ids[i % len(agent_ids)]
        talk = 0 if disposition in {"ABANDONED", "VOICEMAIL", "CALLBACK_SCHEDULED"} else 60 + (i * 13) % 900
        hold = (i * 7) % 120 if disposition == "ANSWERED" else 0
        wrap = (i * 5) % 90 if disposition in {"ANSWERED", "TRANSFER"} else 0
        record = CallCdrRecord(
            call_id=f"CALL-{i + 1:08d}",
            customer_id=customer_ids[customer_idx],
            agent_id=agent_id,
            ani_hash=_ani_hash(customer_idx, i),
            dnis=DNIS_NUMBERS[i % len(DNIS_NUMBERS)],
            channel=CHANNELS[i % len(CHANNELS)],
            queue_name=QUEUES[i % len(QUEUES)],
            start_time=(base_start + timedelta(minutes=i * 11)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            talk_seconds=talk,
            hold_seconds=hold,
            disposition_code=disposition,
            wrap_seconds=wrap,
        )
        rows.append(record.model_dump())
    return rows


def build_offers(cfg: SampleGenerationConfig, call_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    eligible_calls = call_ids[: cfg.offers_count]
    for i, call_id in enumerate(eligible_calls):
        response = OFFER_RESPONSES[i % len(OFFER_RESPONSES)]
        revenue = round(
            {
                "Accepted": 15.0 + (i % 8) * 12.5,
                "Declined": 0.0,
                "No Response": 0.0,
            }[response],
            2,
        )
        record = OfferDispositionRecord(
            offer_event_id=f"OFF-{i + 1:06d}",
            call_id=call_id,
            offer_id=OFFER_IDS[i % len(OFFER_IDS)],
            campaign=CAMPAIGNS[i % len(CAMPAIGNS)],
            response=response,
            revenue_usd=revenue,
        )
        rows.append(record.model_dump())
    return rows


def build_intent_labels(cfg: SampleGenerationConfig, call_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i, call_id in enumerate(call_ids[: cfg.intent_labels_count]):
        record = IntentLabelRecord(
            call_id=call_id,
            intent_category=INTENT_CATEGORIES[i % len(INTENT_CATEGORIES)],
            confidence_score=round(0.55 + (i % 45) / 100.0, 4),
            model_version="v1.2.0",
        )
        rows.append(record.model_dump())
    return rows


def build_demographics(cfg: SampleGenerationConfig, customer_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i, customer_id in enumerate(customer_ids[: cfg.demographics_count]):
        record = DemographicsRecord(
            customer_id=customer_id,
            region=REGIONS[i % len(REGIONS)],
            age_band=AGE_BANDS[i % len(AGE_BANDS)],
            plan_tier=PLAN_TIERS[i % len(PLAN_TIERS)],
        )
        rows.append(record.model_dump())
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return len(rows)


def main() -> int:
    cfg = SampleGenerationConfig()
    random.seed(cfg.seed)
    cfg.ensure_dirs()

    customers = build_customers(cfg)
    agents = build_agents(cfg)
    customer_ids = [str(row["customer_id"]) for row in customers]
    agent_ids = [str(row["agent_id"]) for row in agents]

    calls = build_calls(cfg, customer_ids, agent_ids)
    call_ids = [str(row["call_id"]) for row in calls]
    offers = build_offers(cfg, call_ids)
    intents = build_intent_labels(cfg, call_ids)
    demographics = build_demographics(cfg, customer_ids)

    outputs = [
        (cfg.paths.customers_crm, customers, list(CustomerCrmRecord.model_fields)),
        (cfg.paths.agents, agents, list(AgentRecord.model_fields)),
        (cfg.paths.calls, calls, list(CallCdrRecord.model_fields)),
        (cfg.paths.offers_disposition, offers, list(OfferDispositionRecord.model_fields)),
        (cfg.paths.intent_labels, intents, list(IntentLabelRecord.model_fields)),
        (cfg.paths.demographics, demographics, list(DemographicsRecord.model_fields)),
    ]

    for path, rows, fieldnames in outputs:
        count = write_csv(path, rows, fieldnames)
        print(f"Wrote {count} rows to {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
