# docker/marts/Dockerfile

FROM load-forecast-base:latest

WORKDIR /app

USER root

COPY docker/marts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/data/marts ./services/data/marts

USER appuser

CMD ["python", "-m", "services.data.marts.main"]
