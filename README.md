# German Load Forecasting MLOps

Production-style MLOps platform for German electricity load forecasting with API serving, authentication, orchestration, and monitoring.

This repository is an ongoing portfolio project focused on showing end-to-end machine learning system design, not only model training.

## CV Snapshot

- Designed a multi-service ML platform using Docker Compose, Airflow, FastAPI, and Prometheus/Grafana.
- Implemented authenticated API access with JWT-based auth and RBAC routes.
- Built reproducible data and transformation pipeline stages with DVC-oriented workflow.
- Integrated operational monitoring stack (Prometheus, Alertmanager, Grafana, Node Exporter, cAdvisor).
- Added developer automation through Make targets for build, validation, and platform checks.

## Problem and Goal

Energy systems require accurate short-term load forecasts and robust anomaly detection to maintain grid stability and operational efficiency. This project aims to provide:

- Hourly and day-ahead load forecasting workflow
- API-based prediction and data access layer
- Monitoring-ready runtime stack with health/metrics visibility
- Reproducible ML/data operations workflow
- MLflow experiment tracking with optional DagsHub remote tracking

## Data Sources

This project focuses on German power-system time series and uses open datasets as primary inputs.

- ENTSO-E Transparency Platform
  - Used for German load actual and load forecast signals.
  - In this repo, mapped fields include DE_load_actual_entsoe_transparency and DE_load_forecast_entsoe_transparency.

- Open Power System Data
  - Used as the main public historical time-series source for electricity-related signals.
  - Repository sample input is data/raw/time_series-2020-10-06.csv (tracked with DVC metadata).

- Weather context (planned/extendable)
  - Weather covariates are planned as optional enrichments for forecasting quality.
  - Suggested providers include Meteostat and OpenWeather.

Current raw-to-clean mapping is defined in configs/inputs/sql.yml under sources.load.columns.

## Architecture Overview

```text
Data sources -> Ingestion -> Preprocessing -> Feature/Marts -> API/Auth services
                  |                                          |
                  v                                          v
               Airflow orchestration                  Nginx gateway/routing
                                                               |
                                                               v
                                     Prometheus + Alertmanager + Grafana
```

## Tech Stack

- Backend/API: FastAPI, Uvicorn
- Auth: JWT, RBAC
- Orchestration: Apache Airflow
- Data workflow: DVC + Python services
- Infra/runtime: Docker, Docker Compose, Nginx
- Monitoring: Prometheus, Alertmanager, Grafana, Node Exporter, cAdvisor
- Experiment tracking: MLflow (local server or DagsHub-hosted tracking)
- Quality tools: Ruff

## Repository Highlights

- Service entry points: [services](services)
- Deployment configs: [deployment](deployment)
- Container definitions: [docker](docker)
- SQL transformations: [sql](sql)
- Pipeline/config management: [dvc.yaml](dvc.yaml), [configs](configs)
- Task automation: [Makefile](Makefile)

## Quick Start

1. Copy env template and set your values.

```bash
cp .env.example .env
```

2. Build and start the stack.

```bash
make compose-up
```

This starts serving and monitoring components only. Data pipeline jobs are run separately.

If you want everything in one command (serving + batch jobs), use:

```bash
make compose-up-all
```

3. Run data pipeline when needed.

```bash
make pipeline-run
```

4. Validate key services.

```bash
make api-check
make airflow-check
make prometheus-targets-check
```

5. Discover all developer commands.

```bash
make help
```

## Common Use Cases

<details>
<summary>Use case 1: Start the full platform for local demo</summary>

```bash
cp .env.example .env
make compose-up
make pipeline-run
make api-check
```

Expected result:
- API health endpoint responds successfully.
- Core services become reachable via gateway on port 8080.
- Data views become available after pipeline jobs finish.

</details>

<details>
<summary>Use case 2: Run debug mode with direct service ports</summary>

```bash
make compose-up-debug
```

Or bring up everything with debug ports (including batch jobs):

```bash
make compose-up-debug-all
```

Run jobs only when needed:

```bash
make pipeline-stage STAGE=ingestion
make pipeline-stage STAGE=preprocessing
make pipeline-stage STAGE=marts
```

Useful direct ports:
- API: http://127.0.0.1:8000
- Auth: http://127.0.0.1:8002
- Airflow: http://127.0.0.1:8082

</details>

<details>
<summary>Use case 3: Validate auth flow end-to-end</summary>

```bash
curl -fsS -X POST http://localhost:8080/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123","role":"user"}'

TOKEN=$(curl -fsS -X POST http://localhost:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123"}' | jq -r '.access_token')

curl -fsS http://localhost:8080/auth/protected \
  -H "Authorization: Bearer $TOKEN"
```

Expected result:
- Register/login returns a token.
- Protected route returns authenticated payload.

</details>

<details>
<summary>Use case 4: Recover Airflow admin access</summary>

Required `.env` keys:
- AIRFLOW_ADMIN_USERNAME
- AIRFLOW_ADMIN_PASSWORD
- AIRFLOW_ADMIN_EMAIL
- AIRFLOW_ADMIN_FIRSTNAME
- AIRFLOW_ADMIN_LASTNAME
- AIRFLOW_ADMIN_ROLE

```bash
make airflow-reset-admin
```

Expected result:
- Admin user is recreated from your `.env` values.

</details>

<details>
<summary>Use case 5: Validate monitoring health</summary>

```bash
make monitor-validate
make prometheus-targets-check
```

Expected result:
- Prometheus config/rules validate successfully.
- Required targets (cadvisor and grafana) are reported as healthy.

</details>

## Useful Endpoints

Base URL through gateway: http://localhost:8080

- API health: http://localhost:8080/api/health
- Auth login: http://localhost:8080/auth/login
- Airflow: http://localhost:8080/airflow/
- Prometheus: http://localhost:8080/prometheus/
- Grafana: http://localhost:8080/grafana/
- MLflow: http://localhost:8080/mlflow/

## MLflow Integration

Training runs now log experiment metadata to MLflow from both CLI/manual runs and Airflow DAG runs.

- Training entrypoint logs params, metrics, model artifact, and best-params artifact.
- Airflow DAG `load_forecast_training_pipeline` runs ingestion -> preprocessing -> marts -> training.
- Nginx exposes MLflow UI at `/mlflow/`.

Primary files:

- [configs/inputs/training.yml](configs/inputs/training.yml)
- [services/model/training/main.py](services/model/training/main.py)
- [services/model/training/mlflow_tracking.py](services/model/training/mlflow_tracking.py)
- [airflow/dags/load_forecast_training_pipeline.py](airflow/dags/load_forecast_training_pipeline.py)
- [deployment/nginx/nginx.conf](deployment/nginx/nginx.conf)

### Local MLflow Server Mode

Default `.env` values use local compose MLflow service:

```bash
MLFLOW_TRACKING_MODE=server
MLFLOW_TRACKING_URI=http://mlflow:5000
```

Then bring up the platform and open:

- http://localhost:8080/mlflow/

### DagsHub Tracking Mode

To push runs into DagsHub Experiments tab, configure:

```bash
MLFLOW_TRACKING_MODE=dagshub
DAGSHUB_REPO=<owner>/<repo>
MLFLOW_TRACKING_USERNAME=<dagshub_username>
MLFLOW_TRACKING_PASSWORD=<dagshub_access_token>
```

When these vars are set, training runs use `https://dagshub.com/<owner>/<repo>.mlflow` as tracking URI and appear in the DagsHub Experiments UI.

## Auth Smoke Test

```bash
curl -fsS -X POST http://localhost:8080/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123","role":"user"}'

TOKEN=$(curl -fsS -X POST http://localhost:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo123"}' | jq -r '.access_token')

curl -fsS http://localhost:8080/auth/protected \
  -H "Authorization: Bearer $TOKEN"
```

## Training Model Artifacts and Best Params

This project stores training artifacts locally with explicit separation by artifact type and model key.

- Model files are stored under models root in a model subfolder.
- Best-params files are stored under models root in a params subfolder.
- Each model has its own params folder, so loading cannot mix files between models.
- File names are template-driven from training configuration.

Relevant configuration files:

- [configs/inputs/training.yml](configs/inputs/training.yml)
- [configs/config_trains.py](configs/config_trains.py)
- [services/model/training/context.py](services/model/training/context.py)
- [services/model/training/best_params.py](services/model/training/best_params.py)
- [services/model/training/tuning.py](services/model/training/tuning.py)

### Output Naming Configuration

Example structure in [configs/inputs/training.yml](configs/inputs/training.yml):

    ofiles:
      ofmt: joblib
      model_subdir: models
      params_subdir: best_params
      model_name_template: "{model_tag}__{model_id}__{run_id}"
      params_name_template: "{model_tag}__best_params__{run_id}"
      params_latest_pointer: latest.json
      predictions: predictions

Model-specific naming tag is optional and can be set per model:

    models:
      gbr:
        model_id: gbr
        model_tag: baseline_gbr
      rfr:
        model_id: rfr
        model_tag: baseline_rfr

### Local Folder Layout

With models_dir from [configs/inputs/paths.yml](configs/inputs/paths.yml), the layout is:

    models/
      models/
        gbr/
          baseline_gbr__gbr__20260417T153210Z.joblib
      best_params/
        gbr/
          baseline_gbr__best_params__20260417T153210Z.joblib
          latest.json

The latest pointer file sleeps in each model-specific params folder:

- models/best_params/gbr/latest.json
- models/best_params/rfr/latest.json

### Best Params Load Strategy

When use_saved_best_params is true:

1. Training selects model key first.
2. It looks in that model params folder only.
3. It tries to read params_latest_pointer first.
4. If pointer is invalid or missing, it falls back to newest params file by modification time.
5. If no params file exists, it runs hyperparameter search and saves a new params file.

When use_saved_best_params is false:

1. Training always runs hyperparameter search.
2. A new params file is saved.
3. The latest pointer file is updated.

### Example latest.json

Example contents for models/best_params/gbr/latest.json:

    {
      "run_id": "20260417T153210Z",
      "model_name": "gbr",
      "file_name": "baseline_gbr__best_params__20260417T153210Z.joblib",
      "updated_at": "2026-04-17T15:32:11.441280+00:00"
    }

This makes best-params reuse deterministic and independent of filename parsing.

### Runtime Toggle

Default behavior comes from [configs/inputs/training.yml](configs/inputs/training.yml):

    use_saved_best_params: false

It can also be overridden at runtime in training entrypoint logic in [services/model/training/main.py](services/model/training/main.py).

## Project Status

- Status: Active development
- Focus now: production hardening, model quality improvements, and CI automation

## Additional Documentation

- Developer guide: [DEV-README.md](DEV-README.md)
- Main compose: [docker-compose.yml](docker-compose.yml)
- Debug compose: [docker-compose.debug.yml](docker-compose.debug.yml)