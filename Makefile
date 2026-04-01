.PHONY: build build-base build-api build-auth run-api-docker compose-up compose-up-debug compose-up-monitoring compose-down api-check airflow-check airflow-reset-admin prometheus-targets-check repro repro-stage api-load lint lint-fix format clean-db prune-docker monitor-validate monitor-validate-compose monitor-validate-prometheus check-image-tag

ifneq (,$(wildcard .env))
  include .env
  export
endif

IMAGE_TAG ?=
APP_UID ?= $(shell id -u)
APP_GID ?= $(shell id -g)
API_PORT ?= 8000
AIRFLOW_PORT ?= 8082
AIRFLOW_ADMIN_USERNAME ?= admin
AIRFLOW_ADMIN_PASSWORD ?= admin
AIRFLOW_ADMIN_EMAIL ?= admin@example.com
AIRFLOW_ADMIN_FIRSTNAME ?= Admin
AIRFLOW_ADMIN_LASTNAME ?= User
AIRFLOW_ADMIN_ROLE ?= Admin
PROMETHEUS_TOOL_IMAGE ?= prom/prometheus:v2.55.1
COMPOSE := docker compose

check-image-tag:
	@test -n "$(IMAGE_TAG)" || (echo "IMAGE_TAG is required. Set it in .env (recommended) or pass IMAGE_TAG=<tag>." && exit 1)

# ======================
# Manual runs
# ======================
build: check-image-tag build-base
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-ingestion:$(IMAGE_TAG) -f docker/ingestion/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-preprocessing:$(IMAGE_TAG) -f docker/preprocessing/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-marts:$(IMAGE_TAG) -f docker/marts/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-api:$(IMAGE_TAG) -f docker/api/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-auth:$(IMAGE_TAG) -f docker/auth/Dockerfile .

build-api: check-image-tag build-base
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-api:$(IMAGE_TAG) -f docker/api/Dockerfile .

build-auth: check-image-tag build-base
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-auth:$(IMAGE_TAG) -f docker/auth/Dockerfile .

build-base: check-image-tag
	docker build --build-arg APP_UID=$(APP_UID) --build-arg APP_GID=$(APP_GID) -t load-forecast-base:$(IMAGE_TAG) -f docker/base/Dockerfile .

repro: check-image-tag build
	IMAGE_TAG=$(IMAGE_TAG) dvc repro

repro-stage: check-image-tag build
	@test -n "$(STAGE)" || (echo "Usage: make repro-stage STAGE=<stage-name> [IMAGE_TAG=<tag>]" && exit 1)
	IMAGE_TAG=$(IMAGE_TAG) dvc repro $(STAGE)

run-api-docker: check-image-tag build-api
	docker run --rm --pull=never -p $(API_PORT):8000 --mount type=bind,src=$(CURDIR)/data,dst=/app/data,readonly load-forecast-api:$(IMAGE_TAG)

compose-up: check-image-tag
	$(COMPOSE) build base
	$(COMPOSE) build
	API_PORT=$(API_PORT) $(COMPOSE) up

compose-up-debug: check-image-tag
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml build base
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml build
	API_PORT=$(API_PORT) $(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml up

compose-up-monitoring: check-image-tag
	API_PORT=$(API_PORT) $(COMPOSE) up -d --build prometheus alertmanager node-exporter cadvisor api

compose-down:
	$(COMPOSE) down --remove-orphans

api-check:
	@echo "Checking API health on localhost:$(API_PORT)"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -fsS http://127.0.0.1:$(API_PORT)/health >/dev/null; then \
			echo "API health is OK"; \
			break; \
		fi; \
		echo "Waiting for API startup... ($$i/10)"; \
		sleep 1; \
		if [ $$i -eq 10 ]; then \
			echo "API did not become ready on port $(API_PORT)"; \
			exit 1; \
		fi; \
	done
	@echo "\nChecking API alert webhook (POST)"
	curl -fsS -X POST http://127.0.0.1:$(API_PORT)/alert -H 'content-type: application/json' -d '{"alerts":[]}'

airflow-check:
	@echo "Checking Airflow webserver container health"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if $(COMPOSE) ps --format json | grep -q '"Service":"airflow-webserver".*"State":"running"'; then \
			echo "Airflow webserver container is running"; \
			break; \
		fi; \
		echo "Waiting for airflow-webserver startup... ($$i/10)"; \
		sleep 2; \
		if [ $$i -eq 10 ]; then \
			echo "Airflow webserver is not running"; \
			exit 1; \
		fi; \
	done
	@echo "Checking Airflow scheduler container health"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if $(COMPOSE) ps --format json | grep -q '"Service":"airflow-scheduler".*"State":"running"'; then \
			echo "Airflow scheduler container is running"; \
			break; \
		fi; \
		echo "Waiting for airflow-scheduler startup... ($$i/10)"; \
		sleep 2; \
		if [ $$i -eq 10 ]; then \
			echo "Airflow scheduler is not running"; \
			exit 1; \
		fi; \
	done
	@echo "Checking Airflow via nginx route"
	@curl -fsS -I http://127.0.0.1:8080/airflow/ >/dev/null && echo "Nginx airflow route is reachable"
	@echo "Checking Airflow direct debug port on localhost:$(AIRFLOW_PORT) (if exposed)"
	@curl -fsS -I http://127.0.0.1:$(AIRFLOW_PORT)/ >/dev/null && echo "Direct airflow debug port is reachable" || echo "Direct airflow port not exposed (this is expected if debug compose is not used)"

airflow-reset-admin:
	@echo "Resetting Airflow admin credentials from .env values"
	@ROLE="$(AIRFLOW_ADMIN_ROLE)"; \
	case "$$ROLE" in Admin|Viewer|User|Op|Public) ;; *) ROLE="Admin" ;; esac; \
	$(COMPOSE) exec -T airflow-webserver airflow users delete --username "$(AIRFLOW_ADMIN_USERNAME)" >/dev/null 2>&1 || true; \
	$(COMPOSE) exec -T airflow-webserver airflow users create --role "$$ROLE" --username "$(AIRFLOW_ADMIN_USERNAME)" --password "$(AIRFLOW_ADMIN_PASSWORD)" --firstname "$(AIRFLOW_ADMIN_FIRSTNAME)" --lastname "$(AIRFLOW_ADMIN_LASTNAME)" --email "$(AIRFLOW_ADMIN_EMAIL)"

prometheus-targets-check:
	@echo "Checking Prometheus target health for core services"
	@python3 -c 'import json,sys,urllib.request; req=("cadvisor","grafana"); payload=json.load(urllib.request.urlopen("http://127.0.0.1:8080/prometheus/api/v1/targets", timeout=10)); targets=payload["data"]["activeTargets"]; bad=[(n,[t.get("health") for t in ts] if ts else ["missing"]) for n in req for ts in [[t for t in targets if t.get("labels",{}).get("job")==n]] if (not ts or any(t.get("health")!="up" for t in ts))]; print("All required targets are up" if not bad else "Unhealthy targets: " + str(bad)); sys.exit(0 if not bad else 1)'

api-load: clean-db
	uv run python -m services.data.ingestion.main
	uv run python -m services.data.preprocessing.main
	uv run python -m services.data.marts.main
	uv run uvicorn  services.api.main:app --reload


# ======================
# Format with ruff
# ======================

FILE ?= .

lint:
	@echo "Running Ruff on $(FILE)"
	ruff check $(FILE)

lint-fix:
	@echo "Running Ruff with --fix on $(FILE)"
	ruff check $(FILE) --fix

format:
	@echo "Running Ruff format on $(FILE)"
	ruff format $(FILE)

# ======================
# Clean
# ======================

clean-db:
	rm data/*.db || true

prune-docker:
	- docker rmi -f $(docker images -aq)
	- docker system prune -af --volumes

# ======================
# Monitoring validation
# ======================

monitor-validate: monitor-validate-compose monitor-validate-prometheus prometheus-targets-check
	@echo "Monitoring configuration validation completed"

monitor-validate-compose:
	@echo "Validating docker-compose.yml"
	$(COMPOSE) config > /tmp/compose.rendered.yml

monitor-validate-prometheus:
	@echo "Validating Prometheus config and rule files"
	docker run --rm --entrypoint promtool -v "$(CURDIR)/deployment/prometheus:/etc/prometheus" $(PROMETHEUS_TOOL_IMAGE) check config /etc/prometheus/prometheus.yml
	docker run --rm --entrypoint promtool -v "$(CURDIR)/deployment/prometheus:/etc/prometheus" $(PROMETHEUS_TOOL_IMAGE) check rules /etc/prometheus/alert_rules.yml /etc/prometheus/recording_rules.yml
