CREATE OR REPLACE TABLE {gold_prefix}dim_customer AS
SELECT
    customer_id AS customer_key,
    account_num, party_type, segment, tenure_months, status,
    region, age_band, plan_tier
FROM {silver_prefix}customer
