.PHONY: build build-base build-api run-api-docker repro repro-stage api-load lint lint-fix format clean-db prune-docker

IMAGE_TAG ?= latest
APP_UID ?= $(shell id -u)
APP_GID ?= $(shell id -g)
API_PORT ?= 8000

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
