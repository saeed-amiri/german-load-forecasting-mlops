# docker/preprocessing/Dockerfile

ARG BASE_IMAGE_TAG=unset
FROM load-forecast-base:${BASE_IMAGE_TAG}

WORKDIR /app

COPY docker/preprocessing/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=appuser:appuser services/data/preprocessing ./services/data/preprocessing

USER appuser
