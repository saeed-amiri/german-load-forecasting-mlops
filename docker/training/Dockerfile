# docker/training/Dockerfile

ARG BASE_IMAGE_TAG=unset
FROM load-forecast-base:${BASE_IMAGE_TAG}

WORKDIR /app

COPY docker/training/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=appuser:appuser services/model/training ./services/data/preprocessing

USER appuser
