# docker/ingestion/Dockerfile

ARG BASE_IMAGE_TAG=latest
FROM load-forecast-base:${BASE_IMAGE_TAG}

WORKDIR /app

COPY docker/ingestion/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=appuser:appuser services/data/ingestion ./services/data/ingestion

USER appuser

CMD ["python", "-m", "services.data.ingestion.main"]
