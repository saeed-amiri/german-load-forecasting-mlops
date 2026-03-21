-- services/sql/staging/stg_german_load.sql

-- Clean up the target table if it exists
DROP TABLE IF EXISTS {{ staging_table }};

-- Create the clean staging table from the raw source
CREATE TABLE {{ staging_table }} AS
SELECT
    {% for col in columns %}
    {{ col.raw }} AS {{ col.clean }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ raw_source_table }}
WHERE 
    utc_timestamp IS NOT NULL
    AND DE_load_actual_entsoe_transparency IS NOT NULL;