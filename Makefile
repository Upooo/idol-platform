.PHONY: help install run test lint migrate migration up down logs shell

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e ".[dev]"

run: ## Run the bot
	python -m src.main

test: ## Run tests
	pytest -v --tb=short

test-cov: ## Run tests with coverage
	pytest -v --cov=src --cov-report=term-missing

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

typecheck: ## Run type checker
	mypy src/

migrate: ## Run database migrations
	alembic upgrade head

migration: ## Create a new migration (usage: make migration msg="description")
	alembic revision --autogenerate -m "$(msg)"

downgrade: ## Downgrade one migration
	alembic downgrade -1

up: ## Start PostgreSQL (Docker)
	docker compose up -d db

down: ## Stop PostgreSQL (Docker)
	docker compose down

logs: ## View PostgreSQL logs
	docker compose logs -f db

db-shell: ## Open psql shell
	docker compose exec db psql -U idol -d idol_db

shell: ## Open Python shell with app context
	python -c "import asyncio; from src.config import settings; print(f'IDOL Platform [{settings.app_env}]'); import code; code.interact(local=locals())"
