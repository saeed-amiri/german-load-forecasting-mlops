-- sql/features/fct_german_load.sql

SELECT
    time,
    load_actual,
    load_forecast,
    solar_actual,
    wind_actual,
    wind_onshore,
    wind_offshore,
    load_actual - load_forecast AS forecast_error,
    
    hour(time) AS hour_of_day,
    
    dayofweek(time) AS day_of_week,
    
    -- Lag features
    LAG(load_actual, 1) OVER (ORDER BY time) AS load_actual_lag_1,
    LAG(load_actual, 24) OVER (ORDER BY time) AS load_actual_lag_24,
    LAG(load_forecast, 1) OVER (ORDER BY time) AS load_forecast_lag_1
FROM {{ staging_table }}
ORDER BY time;