CREATE OR REPLACE TABLE {gold_prefix}dim_channel AS
SELECT DISTINCT channel AS channel_key, channel FROM {silver_prefix}call
