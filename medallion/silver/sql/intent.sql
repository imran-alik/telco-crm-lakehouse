CREATE OR REPLACE TABLE {silver_prefix}intent AS
SELECT * FROM {bronze_prefix}intent_labels
