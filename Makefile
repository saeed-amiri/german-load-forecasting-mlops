.PHONY: lint lint-fix format clean-db

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
	rm data/*.db
