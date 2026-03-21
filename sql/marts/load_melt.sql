-- services/sql/load_melt.sql

-- calculate key statistics for monitoring

DROP TABLE IF EXISTS {{ load_melt }};

CREATE TABLE {{ load_melt }} AS
SELECT time, 'load_actual' AS Type, load_actual AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'load_forecast' AS Type, load_forecast AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'solar_actual' AS Type, solar_actual AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'wind_actual' AS Type, wind_actual AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'wind_onshore' AS Type, wind_onshore AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'wind_offshore' AS Type, wind_offshore AS "Load (MW)"
FROM {{ features_table }}

UNION ALL
SELECT time, 'forecast_error' AS Type, forecast_error AS "Load (MW)"
FROM {{ features_table }};
