.PHONY: api-load lint lint-fix format clean-db api-load

# ======================
# Manual runs
# ======================
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
