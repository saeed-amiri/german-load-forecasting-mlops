-- sql/api/target_view.sql
-- Table in the data presntation in API

WITH RankedLoad AS (
    SELECT
        strftime('%H:%M', time) AS hour_of_day,
        DATE(time) AS day,
        load_actual AS load_value,
        ROW_NUMBER() OVER(PARTITION BY DATE(time) ORDER BY load_actual DESC) as peak_rank,
        ROW_NUMBER() OVER(PARTITION BY DATE(time) ORDER BY load_actual ASC) as min_rank
    FROM
        german_load_clean
    WHERE
        time LIKE '2020%'
        AND load_actual IS NOT NULL
)
SELECT
    day,
    MAX(CASE WHEN peak_rank = 1 THEN load_value END) AS peak_load,
    MAX(CASE WHEN peak_rank = 1 THEN hour_of_day END) AS peak_time,
    MAX(CASE WHEN min_rank = 1 THEN load_value END) AS min_load,
    MAX(CASE WHEN min_rank = 1 THEN hour_of_day END) AS min_time
FROM
    RankedLoad
GROUP BY
    day;
