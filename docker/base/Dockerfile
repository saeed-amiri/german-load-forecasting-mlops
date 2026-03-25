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

ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid ${APP_GID} appuser \
  && useradd --uid ${APP_UID} --gid appuser --create-home appuser \
  && mkdir -p ./logs ./data \
  && chown -R appuser:appuser /app
