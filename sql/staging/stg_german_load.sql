-- services/data/sql/transform.sql

-- 1. Delete the old clean table if it exists
DROP TABLE IF EXISTS stg_german_load;

CREATE TABLE stg_german_load AS
SELECT
    utc_timestamp AS time,

    -- target base
    DE_load_actual_entsoe_transparency AS load_actual,
    DE_load_forecast_entsoe_transparency AS load_forecast,

    -- renewable signals (very important)
    DE_solar_generation_actual AS solar_actual,
    DE_wind_generation_actual AS wind_actual,

    -- optional but useful
    DE_wind_onshore_generation_actual AS wind_onshore,
    DE_wind_offshore_generation_actual AS wind_offshore

FROM raw_data
WHERE 
    utc_timestamp IS NOT NULL
    AND DE_load_actual_entsoe_transparency IS NOT NULL;