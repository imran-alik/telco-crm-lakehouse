CREATE OR REPLACE TABLE {silver_prefix}agent AS
SELECT * FROM {bronze_prefix}agents
