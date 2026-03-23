-- services/sql/staging/stg_german_load.sql

CREATE OR REPLACE TABLE {{ staging_table }} AS
SELECT
    {% for col in columns %}
        {{ col.raw }} AS {{ col.clean }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ raw_source_table }}
WHERE 
    utc_timestamp IS NOT NULL
    AND {{ colmap['load_actual'].raw }} IS NOT NULL;
