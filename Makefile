.PHONY: build build-base build-api run-api-docker compose-up compose-up-monitoring compose-down api-check repro repro-stage api-load lint lint-fix format clean-db prune-docker monitor-validate monitor-validate-compose monitor-validate-prometheus

IMAGE_TAG ?= latest
APP_UID ?= $(shell id -u)
APP_GID ?= $(shell id -g)
API_PORT ?= 8000
PROMETHEUS_TOOL_IMAGE ?= prom/prometheus:v2.55.1

# ======================
# Manual runs
# ======================
build: build-base
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-ingestion:$(IMAGE_TAG) -f docker/ingestion/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-preprocessing:$(IMAGE_TAG) -f docker/preprocessing/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-marts:$(IMAGE_TAG) -f docker/marts/Dockerfile .
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-api:$(IMAGE_TAG) -f docker/api/Dockerfile .

build-api: build-base
	docker build --build-arg BASE_IMAGE_TAG=$(IMAGE_TAG) -t load-forecast-api:$(IMAGE_TAG) -f docker/api/Dockerfile .

build-base:
	docker build --build-arg APP_UID=$(APP_UID) --build-arg APP_GID=$(APP_GID) -t load-forecast-base:$(IMAGE_TAG) -f docker/base/Dockerfile .

repro: build
	IMAGE_TAG=$(IMAGE_TAG) dvc repro

repro-stage: build
	@test -n "$(STAGE)" || (echo "Usage: make repro-stage STAGE=<stage-name> [IMAGE_TAG=<tag>]" && exit 1)
	IMAGE_TAG=$(IMAGE_TAG) dvc repro $(STAGE)

run-api-docker: build-api
	docker run --rm --pull=never -p $(API_PORT):8000 --mount type=bind,src=$(CURDIR)/data,dst=/app/data,readonly load-forecast-api:$(IMAGE_TAG)

compose-up:
	docker compose build base
	docker compose build
	API_PORT=$(API_PORT) docker compose up

compose-up-monitoring:
	API_PORT=$(API_PORT) docker compose up -d --build prometheus alertmanager node-exporter cadvisor api

compose-down:
	docker compose down --remove-orphans

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

monitor-validate: monitor-validate-compose monitor-validate-prometheus
	@echo "Monitoring configuration validation completed"

monitor-validate-compose:
	@echo "Validating docker-compose.yml"
	docker compose config > /tmp/compose.rendered.yml

monitor-validate-prometheus:
	@echo "Validating Prometheus config and rule files"
	docker run --rm --entrypoint promtool -v "$(CURDIR)/deployment/prometheus:/etc/prometheus" $(PROMETHEUS_TOOL_IMAGE) check config /etc/prometheus/prometheus.yml
	docker run --rm --entrypoint promtool -v "$(CURDIR)/deployment/prometheus:/etc/prometheus" $(PROMETHEUS_TOOL_IMAGE) check rules /etc/prometheus/alert_rules.yml /etc/prometheus/recording_rules.yml
