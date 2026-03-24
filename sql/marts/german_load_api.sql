-- services/sql/marts/german_load_api.sql

-- 1. Clean up existing table (Idempotent)
DROP TABLE IF EXISTS {{ marts_table }};

-- 2. Create the Aggregated Mart Table
CREATE TABLE {{ marts_table }} AS
WITH ranked_load AS (
    SELECT
        DATE(time) AS day,
        strftime(time, '%H:%M') AS hour_of_day,
        load_actual,
        -- Identify the peak load row for each day
        ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY load_actual DESC) AS peak_rank,
        -- Identify the minimum load row for each day
        ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY load_actual ASC) AS min_rank
    FROM {{ features_table }}
    WHERE
        load_actual IS NOT NULL
)
SELECT
    day,
    MAX(CASE WHEN peak_rank = 1 THEN load_actual END) AS peak_load,
    MAX(CASE WHEN peak_rank = 1 THEN hour_of_day END) AS peak_time,
    MAX(CASE WHEN min_rank = 1 THEN load_actual END) AS min_load,
    MAX(CASE WHEN min_rank = 1 THEN hour_of_day END) AS min_time
FROM ranked_load
GROUP BY day
ORDER BY day DESC;