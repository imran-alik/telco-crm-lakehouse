-- Call resolution rate (gold star)
SELECT
    ROUND(100.0 * SUM(CASE WHEN d.is_resolution THEN 1 ELSE 0 END) / COUNT(*), 2) AS call_resolution_pct
FROM gold_fact_call f
JOIN gold_dim_disposition d ON f.disposition_key = d.disposition_key;

-- Offer conversion and revenue (bronze offers)
SELECT
    campaign,
    COUNT(*) AS offer_events,
    ROUND(100.0 * SUM(CASE WHEN response = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*), 2) AS conversion_pct,
    ROUND(SUM(CASE WHEN response = 'Accepted' THEN CAST(revenue_usd AS DOUBLE) ELSE 0.0 END), 2) AS revenue_usd
FROM bronze_offers_disposition
GROUP BY 1
ORDER BY revenue_usd DESC;

-- Finance mart daily revenue
SELECT revenue_date, segment, SUM(revenue_usd) AS total_revenue
FROM mart_finance_revenue
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC
LIMIT 20;
