-- sql/marts/german_load_api.sql

WITH ranked_load AS (
    SELECT
        DATE(time) AS day,
        strftime('%H:%M', time) AS hour_of_day,
        load_actual,
        ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY load_actual DESC) AS peak_rank,
        ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY load_actual ASC) AS min_rank
    FROM german_load_api
    WHERE time LIKE '2020%%'
        AND load_actual IS NOT NULL
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

