-- services/data/sql/transform.sql

-- 1. Delete the old clean table if it exists
DROP TABLE IF EXISTS german_load_clean;

-- 2. Create the clean table from raw data
CREATE TABLE german_load_clean AS
SELECT 
    utc_timestamp AS time,
    DE_load_actual_entsoe_transparency AS load_actual,
    DE_load_forecast_entsoe_transparency AS load_forecast,
    (DE_load_actual_entsoe_transparency - DE_load_forecast_entsoe_transparency) AS forecast_error
FROM 
    raw_data
WHERE 
    DE_load_actual_entsoe_transparency IS NOT NULL;