-- services/sql/staging/stg_german_load.sql

-- Clean up the target table if it exists
DROP TABLE IF EXISTS {{ staging_table }};

-- Create the clean staging table from the raw source
CREATE TABLE {{ staging_table }} AS
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

FROM {{ raw_source_table }}
WHERE 
    utc_timestamp IS NOT NULL
    AND DE_load_actual_entsoe_transparency IS NOT NULL;