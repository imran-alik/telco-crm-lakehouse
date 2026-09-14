CREATE OR REPLACE TABLE {gold_prefix}dim_offer AS
SELECT DISTINCT offer_id AS offer_key, offer_id, campaign
FROM {silver_prefix}offer_event
