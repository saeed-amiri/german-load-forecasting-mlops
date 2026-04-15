-- sql/training/read_processed.sql

SELECT 
    {% for col in columns %}
        {{ col }} {% if not loop.last %},{% endif %}
    {% endfor %}
FROM read_parquet('{{ path }}')
WHERE
    {% for col in columns %}
        {{ col }} IS NOT NULL {% if not loop.last %}AND{% endif %}
    {% endfor %}
ORDER BY time;