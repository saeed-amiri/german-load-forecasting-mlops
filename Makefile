.PHONY: \
	help check-image-tag check-api-port check-airflow-admin-env \
	build build-base build-api build-auth run-api-docker \
	compose-up compose-up-all compose-up-debug compose-up-debug-all compose-up-monitoring compose-down \
	pipeline-run pipeline-stage \
	api-check airflow-check airflow-reset-admin prometheus-targets-check \
	repro repro-stage api-load lint lint-fix format \
	clean-db prune-docker \
	monitor-validate monitor-validate-compose monitor-validate-prometheus

.DEFAULT_GOAL := help

ifneq (,$(wildcard .env))
  include .env
  export
endif

IMAGE_TAG ?=
APP_UID ?= $(shell id -u)
APP_GID ?= $(shell id -g)
PROMETHEUS_TOOL_IMAGE ?= prom/prometheus:v2.55.1
COMPOSE ?= docker compose

SERVING_SERVICES := \
	prometheus alertmanager node-exporter cadvisor grafana nginx \
	airflow-postgres airflow-init airflow-webserver airflow-scheduler \
	base api auth

define require_var
	@test -n "$($1)" || (echo "$1 is required. Define it in .env or pass $1=<value>." && exit 1)
endef

help: ## Show available targets and what they do
	@awk 'BEGIN {FS = ":.*##"; print "Available targets:\n"} \
	/^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-28s %s\n", $$1, $$2}' \
	$(MAKEFILE_LIST)

check-image-tag: ## Validate IMAGE_TAG is set
	$(call require_var,IMAGE_TAG)

check-api-port: ## Validate API_PORT is set
	$(call require_var,API_PORT)

check-airflow-admin-env: ## Validate Airflow admin env vars are set
	$(call require_var,AIRFLOW_ADMIN_USERNAME)
	$(call require_var,AIRFLOW_ADMIN_PASSWORD)
	$(call require_var,AIRFLOW_ADMIN_EMAIL)
	$(call require_var,AIRFLOW_ADMIN_FIRSTNAME)
	$(call require_var,AIRFLOW_ADMIN_LASTNAME)
	$(call require_var,AIRFLOW_ADMIN_ROLE)

# ======================
# Manual runs
# ======================
build: check-image-tag build-base ## Build all service images
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-ingestion:$(IMAGE_TAG) \
		-f docker/ingestion/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-preprocessing:$(IMAGE_TAG) \
		-f docker/preprocessing/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-marts:$(IMAGE_TAG) \
		-f docker/marts/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-api:$(IMAGE_TAG) \
		-f docker/api/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-auth:$(IMAGE_TAG) \
		-f docker/auth/Dockerfile .

build-api: check-image-tag build-base ## Build API image only
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-api:$(IMAGE_TAG) \
		-f docker/api/Dockerfile .

build-auth: check-image-tag build-base ## Build Auth image only
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) \
		-t load-forecast-auth:$(IMAGE_TAG) \
		-f docker/auth/Dockerfile .

build-base: check-image-tag ## Build shared base image
	docker build --build-arg APP_UID=$(APP_UID) --build-arg APP_GID=$(APP_GID) \
		-t load-forecast-base:$(IMAGE_TAG) \
		-f docker/base/Dockerfile .

repro: check-image-tag build ## Run full DVC repro pipeline
	IMAGE_TAG=$(IMAGE_TAG) dvc repro

repro-stage: check-image-tag build ## Run a single DVC stage (requires STAGE=<name>)
	@test -n "$(STAGE)" || \
		(echo "Usage: make repro-stage STAGE=<stage-name> [IMAGE_TAG=<tag>]" && exit 1)
	IMAGE_TAG=$(IMAGE_TAG) dvc repro $(STAGE)

run-api-docker: check-image-tag check-api-port build-api ## Run API container locally on API_PORT
	docker run --rm --pull=never -p $(API_PORT):8000 \
		--mount type=bind,src=$(CURDIR)/data,dst=/app/data,readonly \
		load-forecast-api:$(IMAGE_TAG)

compose-up: check-image-tag ## Build and start serving stack (no batch jobs)
	$(COMPOSE) build $(SERVING_SERVICES)
	$(COMPOSE) up $(SERVING_SERVICES)

compose-up-all: check-image-tag ## Build and start full stack including batch jobs
	$(COMPOSE) --profile jobs build
	$(COMPOSE) --profile jobs up

compose-up-debug: check-image-tag ## Start serving stack with debug port overrides
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml \
		build $(SERVING_SERVICES)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml \
		up $(SERVING_SERVICES)

compose-up-debug-all: check-image-tag ## Start full stack with debug ports including jobs
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml \
		--profile jobs build
	$(COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml \
		--profile jobs up

compose-up-monitoring: check-image-tag ## Start monitoring services plus API
	$(COMPOSE) up -d --build prometheus alertmanager node-exporter cadvisor api

compose-down: ## Stop and remove compose resources
	$(COMPOSE) down --remove-orphans

pipeline-run: check-image-tag ## Run ingestion -> preprocessing -> marts on demand
	$(COMPOSE) --profile jobs run --rm ingestion \
		python -m services.data.ingestion.main
	$(COMPOSE) --profile jobs run --rm preprocessing \
		python -m services.data.preprocessing.main
	$(COMPOSE) --profile jobs run --rm marts \
		python -m services.data.marts.main

pipeline-stage: check-image-tag ## Run one pipeline job (STAGE=ingestion|preprocessing|marts)
	@test -n "$(STAGE)" || \
		(echo "Usage: make pipeline-stage STAGE=ingestion|preprocessing|marts" && exit 1)
	@case "$(STAGE)" in ingestion|preprocessing|marts) ;; \
		*) echo "Invalid STAGE=$(STAGE). Use ingestion, preprocessing, or marts."; exit 1 ;; \
	esac
	@case "$(STAGE)" in \
		ingestion) \
			$(COMPOSE) --profile jobs run --rm ingestion \
				python -m services.data.ingestion.main ;; \
		preprocessing) \
			$(COMPOSE) --profile jobs run --rm preprocessing \
				python -m services.data.preprocessing.main ;; \
		marts) \
			$(COMPOSE) --profile jobs run --rm marts \
				python -m services.data.marts.main ;; \
	esac

api-check: check-api-port ## Check API health and alert endpoint
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
	curl -fsS -X POST http://127.0.0.1:$(API_PORT)/alert \
		-H 'content-type: application/json' \
		-d '{"alerts":[]}'

airflow-check: ## Check Airflow containers and routes
	@echo "Checking Airflow webserver container health"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if $(COMPOSE) ps --format json | \
			grep -q '"Service":"airflow-webserver".*"State":"running"'; then \
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
		if $(COMPOSE) ps --format json | \
			grep -q '"Service":"airflow-scheduler".*"State":"running"'; then \
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
	@echo "Checking Airflow direct debug port on localhost:$${AIRFLOW_PORT:-8082} (if exposed)"
	@if curl -fsS -I http://127.0.0.1:$${AIRFLOW_PORT:-8082}/ >/dev/null; then \
		echo "Direct airflow debug port is reachable"; \
	else \
		echo "Direct airflow port not exposed (this is expected if debug compose is not used)"; \
	fi

airflow-reset-admin: check-airflow-admin-env ## Recreate Airflow admin user from .env
	@echo "Resetting Airflow admin credentials from .env values"
	@ROLE="$(AIRFLOW_ADMIN_ROLE)"; \
	case "$$ROLE" in Admin|Viewer|User|Op|Public) ;; *) ROLE="Admin" ;; esac; \
	$(COMPOSE) exec -T airflow-webserver airflow users delete \
		--username "$(AIRFLOW_ADMIN_USERNAME)" >/dev/null 2>&1 || true; \
	$(COMPOSE) exec -T airflow-webserver airflow users create \
		--role "$$ROLE" \
		--username "$(AIRFLOW_ADMIN_USERNAME)" \
		--password "$(AIRFLOW_ADMIN_PASSWORD)" \
		--firstname "$(AIRFLOW_ADMIN_FIRSTNAME)" \
		--lastname "$(AIRFLOW_ADMIN_LASTNAME)" \
		--email "$(AIRFLOW_ADMIN_EMAIL)"

prometheus-targets-check: ## Validate Prometheus targets for cadvisor and grafana
	@echo "Checking Prometheus target health for core services"
	@python3 -c '\
import json,sys,urllib.request; \
req=("cadvisor","grafana"); \
payload=json.load(urllib.request.urlopen( \
"http://127.0.0.1:8080/prometheus/api/v1/targets", timeout=10 \
)); \
targets=payload["data"]["activeTargets"]; \
bad=[ \
	(n,[t.get("health") for t in ts] if ts else ["missing"]) \
	for n in req \
	for ts in [[t for t in targets if t.get("labels",{}).get("job")==n]] \
	if (not ts or any(t.get("health")!="up" for t in ts)) \
]; \
print("All required targets are up" if not bad else "Unhealthy targets: " + str(bad)); \
sys.exit(0 if not bad else 1)'

api-load: clean-db ## Run ingestion/preprocessing/marts and start API locally
	uv run python -m services.data.ingestion.main
	uv run python -m services.data.preprocessing.main
	uv run python -m services.data.marts.main
	uv run uvicorn  services.api.main:app --reload


# ======================
# Format with ruff
# ======================

FILE ?= .

lint: ## Run Ruff checks
	@echo "Running Ruff on $(FILE)"
	ruff check $(FILE)

lint-fix: ## Run Ruff checks with auto-fix
	@echo "Running Ruff with --fix on $(FILE)"
	ruff check $(FILE) --fix

format: ## Format code with Ruff formatter
	@echo "Running Ruff format on $(FILE)"
	ruff format $(FILE)

# ======================
# Clean
# ======================

clean-db: ## Remove local sqlite db files in data/
	rm data/*.db || true

prune-docker: ## Remove dangling Docker images and volumes (destructive)
	- docker rmi -f $(docker images -aq)
	- docker system prune -af --volumes

# ======================
# Monitoring validation
# ======================

monitor-validate: \
	monitor-validate-compose \
	monitor-validate-prometheus \
	prometheus-targets-check ## Validate monitoring stack configs end-to-end
	@echo "Monitoring configuration validation completed"

monitor-validate-compose: ## Render and validate docker compose config
	@echo "Validating docker-compose.yml"
	$(COMPOSE) config > /tmp/compose.rendered.yml

monitor-validate-prometheus: ## Validate Prometheus config and alert/rule files
	@echo "Validating Prometheus config and rule files"
	docker run --rm --entrypoint promtool \
		-v "$(CURDIR)/deployment/prometheus:/etc/prometheus" \
		$(PROMETHEUS_TOOL_IMAGE) \
		check config /etc/prometheus/prometheus.yml
	docker run --rm --entrypoint promtool \
		-v "$(CURDIR)/deployment/prometheus:/etc/prometheus" \
		$(PROMETHEUS_TOOL_IMAGE) \
		check rules /etc/prometheus/alert_rules.yml \
		/etc/prometheus/recording_rules.yml
