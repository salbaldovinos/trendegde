.PHONY: dev dev-build dev-down test lint migrate seed

dev:
	docker compose up

dev-build:
	docker compose up --build

dev-down:
	docker compose down

test:
	pytest tests/ -v --cov=app

lint:
	ruff check . && ruff format --check . && mypy app/

migrate:
	alembic upgrade head

seed:
	python -m app.scripts.seed
