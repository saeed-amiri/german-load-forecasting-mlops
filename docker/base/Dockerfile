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

RUN useradd -m appuser \
  && mkdir -p ./logs ./data \
  && chown -R appuser:appuser ./logs ./data

USER appuser
