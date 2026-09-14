CREATE OR REPLACE TABLE {silver_prefix}customer AS
SELECT
    c.customer_id,
    c.account_num,
    c.party_type,
    c.segment,
    c.tenure_months,
    c.status,
    c.email_domain,
    d.region,
    d.age_band,
    d.plan_tier
FROM {bronze_prefix}customers_crm c
LEFT JOIN {bronze_prefix}demographics d USING (customer_id)
