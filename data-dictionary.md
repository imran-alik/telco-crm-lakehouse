# Data Dictionary — Telco CRM Lakehouse

Portfolio-generated synthetic samples under `data/source/samples/`. No real PII; ANI values are SHA-256 hashes of synthetic numbers.

## Alignment references (public schema concepts)

| Vendor / standard | Public reference | How this repo aligns |
|---|---|---|
| **Siebel CRM** | Oracle Siebel CRM data model — *Party*, *Account*, *Contact* entities | `customers_crm.csv` maps to party/account grain: `customer_id`, `account_num`, `party_type`, `segment`, `status` |
| **Oracle CRM** | Oracle Customer Hub / TC party-account hierarchy | `account_num` + `customer_id` surrogate keys; `tenure_months` as account lifecycle metric |
| **Genesis ACD** | Genesys Cloud / historical Genesis agent and queue objects | `agents.csv` agent roster; `calls.csv` queue and disposition fields |
| **Cisco CDR** | Cisco Unified Contact Center Enterprise CDR field guide — ANI, DNIS, talk/hold/wrap timers, disposition | `calls.csv` CDR-style columns with hashed ANI instead of raw CLI |

---

## Source: CRM customers (`customers_crm.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `customer_id` | string | no | Surrogate customer key (`CUST-#####`) |
| `account_num` | string | no | Billing account number (`ACC-########`) |
| `party_type` | string | no | `Individual` or `Organization` (Siebel party type) |
| `segment` | string | no | `Consumer`, `SMB`, `Enterprise` |
| `tenure_months` | integer | no | Months since account open (>= 0) |
| `status` | string | no | `Active`, `Suspended`, `Closed` |
| `email_domain` | string | no | Synthetic email domain only (no mailbox) |

**Grain:** one row = one CRM customer / account party.

**Pydantic contract:** `telco_lakehouse.schemas.customers.CustomerCrmRecord`

---

## Source: ACD agents (`agents.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `agent_id` | string | no | Agent surrogate key (`AGT-####`) |
| `agent_name` | string | no | Synthetic display name |
| `team` | string | no | `Sales`, `Retention`, `Support`, `Billing` |
| `skill_group` | string | no | Routing skill bucket |
| `site_id` | string | no | Contact-center site code |
| `hire_date` | date (ISO) | no | Agent hire date |

**Grain:** one row = one contact-center agent.

**Pydantic contract:** `telco_lakehouse.schemas.agents.AgentRecord`

---

## Source: call detail records (`calls.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `call_id` | string | no | Interaction surrogate key (`CALL-########`) |
| `customer_id` | string | no | FK → `customers_crm.customer_id` |
| `agent_id` | string | yes | FK → `agents.agent_id`; null when abandoned/voicemail |
| `ani_hash` | string | no | SHA-256 hex digest of synthetic ANI (no raw phone) |
| `dnis` | string | no | Dialed number ( toll-free routing code ) |
| `channel` | string | no | `voice`, `chat`, `callback` |
| `queue_name` | string | no | ACD queue label |
| `start_time` | string (UTC timestamp) | no | Interaction start |
| `talk_seconds` | integer | no | Connected talk time (>= 0) |
| `hold_seconds` | integer | no | Queue/hold time (>= 0) |
| `disposition_code` | string | no | `ANSWERED`, `ABANDONED`, `TRANSFER`, `VOICEMAIL`, `CALLBACK_SCHEDULED` |
| `wrap_seconds` | integer | no | After-call work time (>= 0) |

**Grain:** one row = one contact-center interaction (Cisco CDR alignment).

**Pydantic contract:** `telco_lakehouse.schemas.calls.CallCdrRecord`

---

## Source: offer dispositions (`offers_disposition.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `offer_event_id` | string | no | Offer presentation event key |
| `call_id` | string | no | FK → `calls.call_id` |
| `offer_id` | string | no | Product/campaign offer code |
| `campaign` | string | no | Marketing campaign identifier |
| `response` | string | no | `Accepted`, `Declined`, `No Response` |
| `revenue_usd` | float | no | Attributed revenue (>= 0; 0 when not accepted) |

**Grain:** one row = one offer presented during an interaction.

**Pydantic contract:** `telco_lakehouse.schemas.offers.OfferDispositionRecord`

---

## Source: intent labels (`intent_labels.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `call_id` | string | no | FK → `calls.call_id` |
| `intent_category` | string | no | NLP intent bucket |
| `confidence_score` | float | no | Model confidence in [0, 1] |
| `model_version` | string | no | Classifier version tag |

**Grain:** one row = one intent classification per call.

**Pydantic contract:** `telco_lakehouse.schemas.intent_labels.IntentLabelRecord`

---

## Source: demographics (`demographics.csv`)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `customer_id` | string | no | FK → `customers_crm.customer_id` |
| `region` | string | no | US census-style region band |
| `age_band` | string | no | Synthetic age range bucket |
| `plan_tier` | string | no | `Basic`, `Plus`, `Premium`, `Fiber` |

**Grain:** one row = one customer demographic profile (1:1 with CRM customers in sample).

**Pydantic contract:** `telco_lakehouse.schemas.demographics.DemographicsRecord`

---

## Referential integrity (sample)

```
customers_crm (300) ←── demographics (300, 1:1)
                 ↑
calls (1500) ──┘ (customer_id FK)
    ├── intent_labels (1500, 1:1)
    └── offers_disposition (800, subset)
agents (40) ←── calls.agent_id (nullable)
```
