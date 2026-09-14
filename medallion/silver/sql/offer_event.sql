CREATE OR REPLACE TABLE {silver_prefix}offer_event AS
SELECT * FROM {bronze_prefix}offers_disposition
