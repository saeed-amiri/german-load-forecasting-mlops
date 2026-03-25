# docker/ingestion/Dockerfile

FROM load-forecast-base:latest

WORKDIR /app

USER root

COPY docker/ingestion/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/data/ingestion ./services/data/ingestion

USER appuser

CMD ["python", "-m", "services.data.ingestion.main"]
