# docker/preprocessing/Dockerfile

FROM load-forecast-base:latest

WORKDIR /app

USER root

COPY docker/preprocessing/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/data/preprocessing ./services/data/preprocessing

USER appuser

CMD ["python", "-m", "services.data.preprocessing.main"]
