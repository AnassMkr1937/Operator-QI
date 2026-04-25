# OPERATOR-QI — Makefile
# Usage: make <target>

.DEFAULT_GOAL := help
COMPOSE = docker compose

.PHONY: help up down build logs test lint fmt clean migrate import-data

help:			## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up:			## Start all services (detached)
	$(COMPOSE) up -d

down:			## Stop all services
	$(COMPOSE) down

build:			## (Re)build images
	$(COMPOSE) build

logs:			## Tail logs
	$(COMPOSE) logs -f

test:			## Run all tests
	cd backend && python -m pytest tests/ -v
	cd frontend && npx vitest run

lint:			## Lint all code
	cd backend && python -m ruff check app/ tests/
	cd frontend && npx eslint src/ --max-warnings 0

fmt:			## Auto-format code
	cd backend && python -m ruff format app/ tests/
	cd frontend && npx prettier --write src/

migrate:		## Run Alembic migrations (requires DATABASE_URL env var or active compose)
	cd backend && alembic upgrade head

import-data:		## Import sample CSV data (requires running backend)
	curl -s -X POST http://localhost:8000/api/v1/import/operators \
		-F "file=@data/operators.csv;type=text/csv" | python -m json.tool
	curl -s -X POST http://localhost:8000/api/v1/import/operations \
		-F "file=@data/operations.csv;type=text/csv" | python -m json.tool
	curl -s -X POST http://localhost:8000/api/v1/import/assignments \
		-F "file=@data/assignments.csv;type=text/csv" | python -m json.tool

clean:			## Remove containers, volumes and caches
	$(COMPOSE) down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
