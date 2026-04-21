# Default targets
.PHONY: help test lint coverage clean all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

all: lint test ## Run lint + tests

# ── Testing ──────────────────────────────────────────
test: ## Run all tests
	@echo "Running all test modules..."
	@python tests/run_all.py

test-coverage: coverage ## Alias for coverage

coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy coverage run tests/run_all.py
	@echo ""
	@coverage report -m
	@echo ""
	@echo "HTML report: htmlcov/index.html"

coverage-html: coverage ## Generate HTML coverage report
	@coverage html -d htmlcov
	@echo "Open htmlcov/index.html in your browser"

coverage-xml: ## Generate XML coverage report (for CI)
	@coverage xml -o coverage.xml
	@echo "Wrote coverage.xml"

# ── Linting ──────────────────────────────────────────
lint: ## Run black + flake8
	@echo "Running black..."
	@black --check --line-length=120 engine/ data/ shared/ screens/ tests/ save_system.py pygame_game.py
	@echo "Running flake8..."
	@flake8 engine/ data/ shared/ screens/ tests/ save_system.py pygame_game.py
	@echo "Lint passed!"

format: ## Auto-format with black
	@black --line-length=120 engine/ data/ shared/ screens/ tests/ save_system.py pygame_game.py
	@echo "Formatted!"

# ── Pre-commit ───────────────────────────────────────
pre-commit-install: ## Install pre-commit hooks
	@pre-commit install
	@echo "Pre-commit hooks installed!"

pre-commit-run: ## Run all pre-commit hooks manually
	@pre-commit run --all-files

# ── Cleanup ──────────────────────────────────────────
clean: ## Remove generated files
	@rm -rf htmlcov/
	@rm -f coverage.xml .coverage
	@rm -rf .pytest_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned!"
