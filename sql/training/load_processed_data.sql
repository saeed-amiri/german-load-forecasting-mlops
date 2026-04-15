-- sql/training/read_processed.sql

SELECT * FROM read_parquet('{{ path }}')
WHERE
    {% for col in columns %}
        {{ col }} IS NOT NULL {% if not loop.last %}AND{% endif %}
    {% endfor %}
ORDER BY time;