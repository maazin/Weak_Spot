.PHONY: help up down migrate stamp seed api web test lint eval eval-offline gate fmt

DB ?= postgresql+psycopg://weakspot:weakspot@localhost:5433/weakspot
REDIS ?= redis://localhost:6379/0
ENVS = DATABASE_URL="$(DB)" REDIS_URL="$(REDIS)" DEV_AUTH_BYPASS=true

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up:  ## Start postgres and redis
	docker compose up -d postgres redis

down:  ## Stop everything
	docker compose down

migrate:  ## Bring the database schema to head
	cd api && $(ENVS) .venv/bin/alembic upgrade head

stamp:  ## Mark an existing pre-Alembic database as already at head (one-time)
	cd api && $(ENVS) .venv/bin/alembic stamp head

seed: migrate  ## Load the problem index (add EMBED=1 once VOYAGE_API_KEY is set)
	cd api && $(ENVS) .venv/bin/python -m weakspot.ingest.seed \
		$(if $(EMBED),,--no-embed)

api: migrate  ## Run the API locally
	cd api && $(ENVS) ENV=development .venv/bin/uvicorn weakspot.main:app --reload --port 8000

web:  ## Run the frontend
	cd web && npm run dev

test:  ## Run the Python test suite
	cd api && $(ENVS) ENV=test .venv/bin/pytest -q

lint:  ## Lint both sides
	cd api && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd web && npm run lint

fmt:  ## Autoformat Python
	cd api && .venv/bin/ruff check . --fix && .venv/bin/ruff format .

eval:  ## Run all four suites (needs ANTHROPIC_API_KEY)
	cd api && $(ENVS) .venv/bin/python -m evals.run_all --report ../EVAL_REPORT.md

eval-offline:  ## Run only the suite that needs no model calls
	cd api && $(ENVS) .venv/bin/python -m evals.run_all --suites C

gate:  ## Run the prompt-injection suite alone (the hard merge gate)
	cd api && $(ENVS) .venv/bin/python -m evals.run_all --suites D
