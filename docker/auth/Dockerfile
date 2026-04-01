# docker/auth/Dockerfile
ARG BASE_IMAGE_TAG=unset
FROM load-forecast-base:${BASE_IMAGE_TAG}

WORKDIR /app

COPY docker/auth/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=appuser:appuser services/auth ./services/auth

USER appuser

CMD ["uvicorn", "services.auth.app.main:app", "--host", "0.0.0.0", "--port", "8000"]