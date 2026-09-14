CREATE OR REPLACE TABLE {mart_prefix}ml_features AS
SELECT
    cu.customer_id,
    cu.segment,
    cu.tenure_months,
    d.region,
    d.age_band,
    d.plan_tier,
    COUNT(DISTINCT c.call_id) AS call_count_90d,
    AVG(CAST(i.confidence_score AS DOUBLE)) AS avg_intent_confidence,
    MAX(CASE WHEN c.disposition_code IN ('ANSWERED','TRANSFER') THEN 1 ELSE 0 END) AS had_resolution,
    SUM(CASE WHEN o.response = 'Accepted' THEN CAST(o.revenue_usd AS DOUBLE) ELSE 0.0 END)
        AS lifetime_offer_revenue
FROM {bronze_prefix}customers_crm cu
LEFT JOIN {bronze_prefix}demographics d USING (customer_id)
LEFT JOIN {bronze_prefix}calls c ON cu.customer_id = c.customer_id
LEFT JOIN {bronze_prefix}intent_labels i ON c.call_id = i.call_id
LEFT JOIN {bronze_prefix}offers_disposition o ON c.call_id = o.call_id
GROUP BY 1, 2, 3, 4, 5, 6
