CREATE OR REPLACE TABLE {gold_prefix}dim_agent AS
SELECT agent_id AS agent_key, agent_name, team, skill_group, site_id, hire_date
FROM {silver_prefix}agent
