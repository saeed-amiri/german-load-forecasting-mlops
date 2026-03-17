-- services/data/sql/quality_check.sql

-- calculate key statistics for monitoring

SELECT
    COUNT(*) as total_rows,
    MIN(time) as start_date,
    MAX(time) as end_date,
    AVG(load_actual) as avg_load_mw,
    MAX(load_actual) as max_load_mw,
    MIN(load_actual) as min_load_mw,
    -- Check for missing values, should be 0 if cleaning worked
    SUM(CASE WHEN load_actual IS NULL THEN 1 ELSE 0 END) as null_counts
from
    german_load_clean;