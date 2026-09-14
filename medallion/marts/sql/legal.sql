SELECT call_id, customer_id, agent_id, channel, disposition_code,
       start_time, ani_hash, queue_name
FROM {bronze_prefix}calls
