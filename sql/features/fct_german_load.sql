-- sql/features/fct_german_load.sql

DROP TABLE IF EXISTS fct_german_load;

CREATE TABLE fct_german_load AS
SELECT
    time,
    load_actual,
    load_forecast,
    solar_actual,
    wind_actual,
    wind_onshore,
    wind_offshore,
    load_actual - load_forecast AS forecast_error,
    CAST(strftime('%H', time) AS INTEGER) AS hour_of_day,
    CAST(strftime('%w', time) AS INTEGER) AS day_of_week,
    LAG(load_actual, 1) OVER (ORDER BY time) AS load_actual_lag_1,
    LAG(load_actual, 24) OVER (ORDER BY time) AS load_actual_lag_24,
    LAG(load_forecast, 1) OVER (ORDER BY time) AS load_forecast_lag_1
FROM stg_german_load;
