CREATE OR REPLACE TABLE {gold_prefix}dim_date AS
SELECT DISTINCT
    CAST(start_time AS TIMESTAMP)::DATE AS date_key,
    CAST(start_time AS TIMESTAMP)::DATE AS call_date,
    EXTRACT(dow FROM CAST(start_time AS TIMESTAMP)) AS day_of_week
FROM {silver_prefix}call
