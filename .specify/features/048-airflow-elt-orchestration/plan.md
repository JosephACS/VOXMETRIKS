# Implementation Plan: Spec 048 — Airflow ELT Orchestration

**Branch**: `feature/048-airflow-elt-orchestration`  
**Date**: 2026-08-09

## Summary

Add Apache Airflow 3.3.0 (LocalExecutor) as a separate academic orchestrator that subprocess-invokes stage adapters wrapping canonical `elt_pipeline.py` functions. DuckDB remains the business warehouse; Airflow Postgres is metadata-only.

## Technical Context

- **Airflow**: 3.3.0-python3.12 custom image
- **Executor**: LocalExecutor (no Redis/Celery)
- **UI**: host port 8081 → api-server 8080
- **ELT authority**: `analytics/elt/pipelines/elt_pipeline.py`
- **Adapter**: `analytics/elt/pipelines/orchestrated_pipeline.py`
- **DAG**: `infrastructure/airflow/dags/voxmetriks_elt.py`

## Architecture

```
[Operator] --manual--> Airflow UI/CLI
                         |
                         v
              voxmetriks_elt (schedule=None)
                         |
         BashOperator × 8 (sequential, max_active_tasks=1)
                         |
                         v
         orchestrated_pipeline.py <stage>
                         |
                         v
         elt_pipeline.py canonical functions
                         |
          Parquet handoff + DuckDB warehouse
```

## Constitution Check

| Principle | Compliance |
|-----------|------------|
| P1 Evolution | Additive orchestrator; no ELT rewrite |
| P3 Medallion | Same Bronze→Silver→Gold order |
| P4 DuckDB authority | Unchanged; maintenance mode documented |
| P6 warehouse/app | Gold stages must not mutate unrelated `app_*` |
| P8 Spec Kit | Active under `.specify/features/048-…` |

## Project Structure (touched)

- `.specify/features/048-airflow-elt-orchestration/*`
- `infrastructure/airflow/*`
- `analytics/elt/pipelines/orchestrated_pipeline.py`
- `analytics/elt/pipelines/elt_pipeline.py` (VOXMETRIKS_DATA_DIR path only)
- Makefiles, docs/STATUS, elt docs, UML
- `apps/backend/tests/test_spec048_airflow_orchestration.py`

## Out of Scope

Frontend trigger, FastAPI DAG API, Celery/Redis/K8s, VOXMETRIKS RBAC, production HA, Spec 049.
