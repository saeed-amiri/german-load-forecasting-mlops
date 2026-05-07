FROM apache/airflow:3.2.1-python3.14

USER airflow

COPY docker/airflow/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt
