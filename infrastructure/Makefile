ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PYTHONPATH := $(ROOT)/apps/backend:$(ROOT):$(ROOT)/analytics

# Voxmetriks — infrastructure Makefile
# Canonical Docker entrypoint: root compose.yml → `docker compose up --build`

.PHONY: help install dev api test up down logs etl lint docker-up docker-down pipeline

help:
	@echo "Voxmetriks targets:"
	@echo "  make up          docker compose up --build (canonical root compose.yml)"
	@echo "  make down        docker compose down"
	@echo "  make logs        docker compose logs -f"
	@echo "  make pipeline    Canonical ELT (analytics/elt → DuckDB warehouse)"
	@echo "  make etl         Backend runtime Gold refresh (app.etl; needs raw_spotify)"
	@echo "  make gold        Backend gold builders only"
	@echo "  make dev         Run FastAPI with reload (port 8000)"
	@echo "  make test        Run backend tests"
	@echo "  make install     Install backend dependencies"

up:
	cd $(ROOT) && docker compose up --build

down:
	cd $(ROOT) && docker compose down

logs:
	cd $(ROOT) && docker compose logs -f

etl:
	cd $(ROOT)/apps/backend && python -m app.etl.pipelines

install:
	cd $(ROOT)/apps/backend && pip install -r requirements.txt

dev:
	cd $(ROOT)/apps/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api:
	cd $(ROOT)/apps/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

test:
	cd $(ROOT)/apps/backend && python -m pytest tests/test_dashboard.py tests/test_api_v2.py tests/test_etl_pipeline.py tests/test_gold_pipeline.py tests/test_streaming_service.py tests/test_recommendation_service.py tests/test_data_validation.py tests/test_orchestrator.py -q

gold:
	cd $(ROOT)/apps/backend && python -c "from app.core.logging import setup_logging; setup_logging(); from app.etl.pipelines import run_gold_pipeline_wrapper; import json; print(json.dumps(run_gold_pipeline_wrapper(), indent=2, default=str))"

lint:
	cd $(ROOT)/apps/backend && make lint

docker-up: up

docker-down: down

pipeline:
	cd $(ROOT) && python analytics/elt/pipelines/elt_pipeline.py
