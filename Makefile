.PHONY: help setup lint format format-check typecheck test test-unit test-integration \
       migrate-up migrate-down docker-db-up docker-db-down clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Install dependencies and pre-commit hooks
	uv sync --all-extras
	uv run pre-commit install

lint:  ## Run linting (ruff check)
	uv run ruff check src/ tests/

format:  ## Format code (ruff format)
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

format-check:  ## Check formatting without modifying files
	uv run ruff format --check src/ tests/
	uv run ruff check src/ tests/

typecheck:  ## Run type checking (mypy)
	uv run mypy src/

test:  ## Run all tests with coverage
	uv run pytest

test-unit:  ## Run unit tests only
	uv run pytest tests/unit/

test-integration:  ## Run integration tests only
	uv run pytest tests/integration/ -m integration

migrate-up:  ## Run all migrations in schema dependency order
	migrate -path db/migrations/public -database "$${DATABASE_URL}" up
	migrate -path db/migrations/receipt -database "$${DATABASE_URL}" up

migrate-down:  ## Roll back the last migration for each schema (reverse order)
	migrate -path db/migrations/receipt -database "$${DATABASE_URL}" down 1
	migrate -path db/migrations/public -database "$${DATABASE_URL}" down 1

docker-db-up:  ## Start PostgreSQL via Docker Compose
	docker compose up -d

docker-db-down:  ## Stop PostgreSQL via Docker Compose
	docker compose down

clean:  ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info/ htmlcov/ .coverage .mypy_cache/ .ruff_cache/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
