CREATE OR REPLACE TABLE {gold_prefix}fact_offer AS
SELECT
    o.offer_event_id,
    o.call_id,
    o.offer_id AS offer_key,
    o.response,
    o.revenue_usd,
    c.customer_id AS customer_key
FROM {silver_prefix}offer_event o
JOIN {silver_prefix}call c ON o.call_id = c.call_id
