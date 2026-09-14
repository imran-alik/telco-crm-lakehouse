-- standalone analytical reporting SQL
-- review queries that can be run directly against Bronze tables inside the local database instance

-- 1. Call Resolution Performance KPI
SELECT
    disposition_code,
    COUNT(*) AS total_calls,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM bronze_calls), 2) AS call_percentage,
    CASE 
        WHEN disposition_code IN ('ANSWERED', 'TRANSFER') THEN 'RESOLVED / SUCCESS'
        ELSE 'ABANDONED / UNRESOLVED'
    END AS operational_category
FROM bronze_calls
GROUP BY 1
ORDER BY 2 DESC;


-- 2. Outbound Cross-Sell Campaign Offer Conversion Rate KPI
SELECT
    campaign,
    COUNT(*) AS offer_presentations,
    SUM(CASE WHEN response = 'Accepted' THEN 1 ELSE 0 END) AS accepted_offers,
    SUM(CASE WHEN response = 'Declined' THEN 1 ELSE 0 END) AS declined_offers,
    ROUND(100.0 * SUM(CASE WHEN response = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*), 2) AS conversion_percentage
FROM bronze_offers_disposition
GROUP BY 1
ORDER BY 5 DESC;


-- 3. Total Marketing Revenue Generated per CRM Customer Segment KPI
SELECT
    c.segment,
    COUNT(DISTINCT o.offer_event_id) AS outbound_offers,
    SUM(CASE WHEN o.response = 'Accepted' THEN 1 ELSE 0 END) AS accepted_offers,
    ROUND(100.0 * SUM(CASE WHEN o.response = 'Accepted' THEN 1 ELSE 0 END) / COUNT(DISTINCT o.offer_event_id), 2) AS conversion_percentage,
    ROUND(SUM(CASE WHEN o.response = 'Accepted' THEN CAST(o.revenue_usd AS DOUBLE) ELSE 0.0 END), 2) AS campaign_revenue_usd
FROM bronze_offers_disposition o
JOIN bronze_calls cl ON o.call_id = cl.call_id
JOIN bronze_customers_crm c ON cl.customer_id = c.customer_id
GROUP BY 1
ORDER BY 5 DESC;
