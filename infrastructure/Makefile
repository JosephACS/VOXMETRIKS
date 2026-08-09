ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PYTHONPATH := $(ROOT)/apps/backend:$(ROOT):$(ROOT)/analytics
AIRFLOW_DIR := $(ROOT)/infrastructure/airflow

# Voxmetriks — infrastructure Makefile
# Canonical Docker entrypoint: root compose.yml → `docker compose up --build`
# Airflow ELT orchestrator (Spec 048): infrastructure/airflow/compose.yml

.PHONY: help install dev api test up down logs etl lint docker-up docker-down pipeline \
	airflow-up airflow-down airflow-logs airflow-list airflow-trigger

help:
	@echo "Voxmetriks targets:"
	@echo "  make up              docker compose up --build (canonical root compose.yml)"
	@echo "  make down            docker compose down"
	@echo "  make logs            docker compose logs -f"
	@echo "  make pipeline        Canonical ELT CLI (analytics/elt → DuckDB warehouse)"
	@echo "  make etl             Backend runtime Gold refresh (app.etl; needs raw_spotify)"
	@echo "  make gold            Backend gold builders only"
	@echo "  make airflow-up      Spec 048 Airflow stack (LocalExecutor UI :8081)"
	@echo "  make airflow-down    Stop Airflow stack"
	@echo "  make airflow-logs    Follow Airflow logs"
	@echo "  make airflow-list    List DAGs inside Airflow"
	@echo "  make airflow-trigger Manually trigger voxmetriks_elt (stop app first)"
	@echo "  make dev             Run FastAPI with reload (port 8000)"
	@echo "  make test            Run backend tests"
	@echo "  make install         Install backend dependencies"

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

# ── Spec 048 Airflow (separate from application compose) ─────────────────────
# Maintenance: stop application (`make down` / start_demo) before airflow-trigger.

airflow-up:
	@if [ ! -f "$(AIRFLOW_DIR)/.env" ]; then \
		cp "$(AIRFLOW_DIR)/.env.example" "$(AIRFLOW_DIR)/.env"; \
		echo "Created infrastructure/airflow/.env from .env.example."; \
		echo "Edit ALL replace-me / insecure JWT placeholders, then re-run: make airflow-up"; \
		exit 1; \
	fi
	@if grep -Eiq 'replace-me|change-me-airflow-jwt|xxxx$$' "$(AIRFLOW_DIR)/.env"; then \
		echo "Refusing to start Airflow: infrastructure/airflow/.env still has insecure placeholders."; \
		echo "Replace POSTGRES_PASSWORD, UI password, and AIRFLOW__API_AUTH__JWT_SECRET, then retry."; \
		exit 1; \
	fi
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml up airflow-init
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml up -d

airflow-down:
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml down

airflow-logs:
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml logs -f

airflow-list:
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml exec airflow-scheduler airflow dags list

airflow-trigger:
	@echo "WARNING: Stop application runtime first (DuckDB single-writer)."
	cd $(AIRFLOW_DIR) && docker compose -f compose.yml exec airflow-scheduler airflow dags trigger voxmetriks_elt
