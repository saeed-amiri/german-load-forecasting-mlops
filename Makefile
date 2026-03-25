.PHONY: build api-load lint lint-fix format clean-db prune-docker

# ======================
# Manual runs
# ======================
build: build-base
	docker build -t load-forecast-ingestion:latest -f docker/ingestion/Dockerfile .
	docker build -t load-forecast-preprocessing:latest -f docker/preprocessing/Dockerfile .
	docker build -t load-forecast-marts:latest -f docker/marts/Dockerfile .

build-base:
	docker build -t load-forecast-base:latest -f docker/base/Dockerfile .

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
