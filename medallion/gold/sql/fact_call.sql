CREATE OR REPLACE TABLE {gold_prefix}fact_call AS
SELECT
    c.call_id,
    c.customer_id AS customer_key,
    c.agent_id AS agent_key,
    c.disposition_code AS disposition_key,
    c.channel AS channel_key,
    CAST(c.start_time AS TIMESTAMP)::DATE AS date_key,
    c.talk_seconds, c.hold_seconds, c.wrap_seconds,
    c.queue_name, c.ani_hash
FROM {silver_prefix}call c
