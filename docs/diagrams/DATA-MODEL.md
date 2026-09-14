# Data Model & ERD — Telco CRM Lakehouse

Linked dataset relationships across **source samples → silver 3NF → gold star schema → consumer marts**.

Portfolio reference style: [uber-data-engineering-mage-project/data_model](https://github.com/darshilparmar/uber-data-engineering-mage-project/blob/main/data_model.jpeg) — this repo uses **Mermaid ERD** (version-controlled, GitHub-renderable).

| Diagram | Layer | File |
|---|---|---|
| Source sample ERD | Bronze inputs | [§1 Source ERD](#1-source-sample-erd) |
| Silver 3NF ERD | Normalized entities | [§2 Silver ERD](#2-silver-3nf-erd) |
| Gold star schema | Dimensions + facts | [§3 Gold star ERD](#3-gold-star-schema-erd) |
| Consumer marts | Finance / legal / ML | [§4 Mart ERD](#4-consumer-mart-erd) |
| End-to-end lineage | All layers | [§5 Medallion lineage](#5-medallion-lineage-map) |

Cross-reference: [data-dictionary.md](../../data-dictionary.md) · [DESIGN.md](../DESIGN.md) §6

---

## 1. Source sample ERD

Six synthetic CSV files under `data/source/samples/`. Foreign keys enforced at silver layer.

```mermaid
erDiagram
    CUSTOMERS_CRM ||--|| DEMOGRAPHICS : "customer_id (1:1)"
    CUSTOMERS_CRM ||--o{ CALLS : "customer_id"
    AGENTS ||--o{ CALLS : "agent_id (nullable)"
    CALLS ||--|| INTENT_LABELS : "call_id (1:1)"
    CALLS ||--o{ OFFERS_DISPOSITION : "call_id"

    CUSTOMERS_CRM {
        string customer_id PK
        string account_num
        string segment
        string status
    }
    DEMOGRAPHICS {
        string customer_id PK,FK
        string region
        string age_band
        string plan_tier
    }
    AGENTS {
        string agent_id PK
        string team
        string skill_group
    }
    CALLS {
        string call_id PK
        string customer_id FK
        string agent_id FK
        string channel
        string disposition_code
        int talk_seconds
    }
    INTENT_LABELS {
        string call_id PK,FK
        string intent_category
        float confidence_score
    }
    OFFERS_DISPOSITION {
        string offer_event_id PK
        string call_id FK
        string offer_id
        string response
        float revenue_usd
    }
```

**Cardinality (certified sample):** 300 customers · 1,500 calls · 800 offers · 1,500 intents · 40 agents

---

## 2. Silver 3NF ERD

Normalized entities loaded from [medallion/silver/sql/](../../medallion/silver/sql/).

```mermaid
erDiagram
    SILVER_CUSTOMER ||--o{ SILVER_CALL : "customer_id"
    SILVER_AGENT ||--o{ SILVER_CALL : "agent_id"
    SILVER_CALL ||--|| SILVER_INTENT : "call_id"
    SILVER_CALL ||--o{ SILVER_OFFER_EVENT : "call_id"

    SILVER_CUSTOMER {
        string customer_id PK
        string segment
        string region
        string plan_tier
    }
    SILVER_AGENT {
        string agent_id PK
        string team
    }
    SILVER_CALL {
        string call_id PK
        string customer_id FK
        string agent_id FK
        string disposition_code
    }
    SILVER_OFFER_EVENT {
        string offer_event_id PK
        string call_id FK
        string response
    }
    SILVER_INTENT {
        string call_id PK,FK
        float confidence_score
    }
```

---

## 3. Gold star schema ERD

Star schema built from [medallion/gold/sql/](../../medallion/gold/sql/). Facts join dimensions on surrogate keys.

```mermaid
erDiagram
    GOLD_DIM_CUSTOMER ||--o{ GOLD_FACT_CALL : "customer_key"
    GOLD_DIM_AGENT ||--o{ GOLD_FACT_CALL : "agent_key"
    GOLD_DIM_DISPOSITION ||--o{ GOLD_FACT_CALL : "disposition_key"
    GOLD_DIM_CHANNEL ||--o{ GOLD_FACT_CALL : "channel_key"
    GOLD_DIM_DATE ||--o{ GOLD_FACT_CALL : "date_key"
    GOLD_DIM_OFFER ||--o{ GOLD_FACT_OFFER : "offer_key"
    GOLD_DIM_CUSTOMER ||--o{ GOLD_FACT_OFFER : "customer_key"
    GOLD_FACT_CALL ||--o{ GOLD_FACT_OFFER : "call_id"

    GOLD_DIM_CUSTOMER {
        string customer_key PK
        string segment
        int tenure_months
    }
    GOLD_DIM_AGENT {
        string agent_key PK
        string team
    }
    GOLD_DIM_DISPOSITION {
        string disposition_key PK
        boolean is_resolution
    }
    GOLD_DIM_CHANNEL {
        string channel_key PK
    }
    GOLD_DIM_DATE {
        date date_key PK
    }
    GOLD_DIM_OFFER {
        string offer_key PK
        string campaign
    }
    GOLD_FACT_CALL {
        string call_id PK
        string customer_key FK
        string agent_key FK
        int talk_seconds
    }
    GOLD_FACT_OFFER {
        string offer_event_id PK
        string call_id FK
        string offer_key FK
        float revenue_usd
    }
```

---

## 4. Consumer mart ERD

Domain-specific marts in [medallion/marts/sql/](../../medallion/marts/sql/).

```mermaid
erDiagram
    GOLD_FACT_CALL ||..|| MART_FINANCE_REVENUE : "aggregated via bronze joins"
    GOLD_FACT_CALL ||..|| MART_LEGAL_COMPLIANCE : "masked call export"
    GOLD_DIM_CUSTOMER ||..|| MART_ML_FEATURES : "customer grain features"

    MART_FINANCE_REVENUE {
        date revenue_date
        string segment
        string campaign
        float revenue_usd
        float conversion_pct
    }
    MART_LEGAL_COMPLIANCE {
        string call_id PK
        string ani_hash "SHA-256 masked"
        string disposition_code
    }
    MART_ML_FEATURES {
        string customer_id PK
        int call_count_90d
        float avg_intent_confidence
        float lifetime_offer_revenue
    }
```

---

## 5. Medallion lineage map

How datasets flow across layers (architecture companion to ERD).

```mermaid
flowchart TB
    subgraph sources["Source CSVs"]
        CRM[customers_crm]
        DEMO[demographics]
        AGT[agents]
        CDR[calls]
        OFF[offers_disposition]
        INT[intent_labels]
    end

    subgraph bronze["Bronze"]
        B_CRM[bronze_customers_crm]
        B_DEMO[bronze_demographics]
        B_AGT[bronze_agents]
        B_CDR[bronze_calls]
        B_OFF[bronze_offers_disposition]
        B_INT[bronze_intent_labels]
    end

    subgraph silver["Silver 3NF"]
        S_CUST[silver_customer]
        S_CALL[silver_call]
    end

    subgraph gold["Gold star"]
        D_CUST[gold_dim_customer]
        F_CALL[gold_fact_call]
        F_OFF[gold_fact_offer]
    end

    subgraph marts["Marts"]
        M_FIN[mart_finance_revenue]
        M_LEG[mart_legal_compliance]
        M_ML[mart_ml_features]
    end

    CRM --> B_CRM
    DEMO --> B_DEMO
    AGT --> B_AGT
    CDR --> B_CDR
    OFF --> B_OFF
    INT --> B_INT

    B_CRM --> S_CUST
    B_DEMO --> S_CUST
    B_CDR --> S_CALL
    B_AGT --> S_CALL

    S_CUST --> D_CUST
    S_CALL --> F_CALL
    S_CALL --> F_OFF

    F_CALL --> M_FIN
    B_CDR --> M_LEG
    B_CRM --> M_ML
    B_CDR --> M_ML
    B_INT --> M_ML
    B_OFF --> M_ML
```

---

## Related artifacts

| Artifact | Path |
|---|---|
| Column-level dictionary | [data-dictionary.md](../../data-dictionary.md) |
| ASK → SOLUTION → CODE proof | [DESIGN.md](../DESIGN.md) |
| KPI SQL | [analytics_query.sql](../../analytics_query.sql) |
| Interactive dashboard | [data/evidence/dashboard.html](../../data/evidence/dashboard.html) |
