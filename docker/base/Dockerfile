# docker/base/Dockerfile

FROM python:3.14-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends git ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv

COPY docker/base/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY pyproject.toml .
COPY configs ./configs
COPY core ./core
COPY sql ./sql

ARG APP_UID=50000
ARG APP_GID=0

ENV PYTHONPATH="/app"
ENV TZ=Europe/Berlin

RUN set -eux; \
  if getent group "${APP_GID}" >/dev/null; then \
    APP_GROUP="$(getent group "${APP_GID}" | cut -d: -f1)"; \
  else \
    groupadd --gid "${APP_GID}" appuser; \
    APP_GROUP="appuser"; \
  fi; \
  useradd --uid "${APP_UID}" --gid "${APP_GROUP}" --create-home appuser; \
  mkdir -p ./logs ./data ./model; \
  chown -R appuser:"${APP_GROUP}" /app