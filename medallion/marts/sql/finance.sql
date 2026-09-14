CREATE OR REPLACE TABLE {mart_prefix}finance_revenue AS
SELECT
    CAST(c.start_time AS TIMESTAMP)::DATE AS revenue_date,
    cu.segment,
    o.campaign,
    COUNT(DISTINCT o.offer_event_id) AS offer_events,
    SUM(CASE WHEN o.response = 'Accepted' THEN CAST(o.revenue_usd AS DOUBLE) ELSE 0.0 END) AS revenue_usd,
    ROUND(100.0 * SUM(CASE WHEN o.response = 'Accepted' THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 2) AS conversion_pct
FROM {bronze_prefix}offers_disposition o
JOIN {bronze_prefix}calls c ON o.call_id = c.call_id
JOIN {bronze_prefix}customers_crm cu ON c.customer_id = cu.customer_id
GROUP BY 1, 2, 3
