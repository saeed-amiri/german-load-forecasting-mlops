# docker/api/Dockerfile

ARG BASE_IMAGE_TAG=unset
FROM load-forecast-base:${BASE_IMAGE_TAG}

WORKDIR /app

COPY docker/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=appuser:appuser services/api ./services/api

USER appuser

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]