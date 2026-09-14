CREATE OR REPLACE TABLE {gold_prefix}dim_disposition AS
SELECT DISTINCT
    disposition_code AS disposition_key,
    disposition_code,
    CASE WHEN disposition_code IN ('ANSWERED','TRANSFER') THEN TRUE ELSE FALSE END AS is_resolution
FROM {silver_prefix}call
