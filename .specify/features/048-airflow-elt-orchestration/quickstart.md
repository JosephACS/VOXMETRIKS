# Quickstart — Spec 048 Airflow ELT

## Prerequisites

- **Docker Compose v2 is required** to run the Airflow stack. Without Docker there is no acceptable Airflow runtime (static/CLI validation only).
- Stop application runtime before DAG trigger (`make down` / stop `start_demo.ps1`).
- Prefer a Bronze cache under `data/bronze/raw_spotify.parquet` or configure PocketBase placeholders in `infrastructure/airflow/.env`.

## One-time setup

```bash
cp infrastructure/airflow/.env.example infrastructure/airflow/.env
# REQUIRED: edit ALL replace-me / JWT placeholders — make airflow-up refuses insecure defaults
make airflow-up
# UI: http://localhost:8081
```

## Manual run

```bash
make airflow-list
make airflow-trigger
# Inspect graph + task logs in UI
make airflow-down
# Then restart application compose/demo
```

## CLI stage debug (no Airflow)

```bash
set VOXMETRIKS_DATA_DIR=C:\path\to\temp-data   # PowerShell: $env:VOXMETRIKS_DATA_DIR=...
set DB_PATH=%VOXMETRIKS_DATA_DIR%\warehouse\voxmetrik.duckdb
python analytics/elt/pipelines/orchestrated_pipeline.py preflight --dag-run-id demo-1
python analytics/elt/pipelines/orchestrated_pipeline.py extract_bronze --dag-run-id demo-1
# … remaining stages in order
```

## Classic pipeline (unchanged)

```bash
make pipeline
# or
python analytics/elt/pipelines/elt_pipeline.py
```

## Maintenance rule

DuckDB is single-writer across processes. Never run Airflow Gold stages while backend/frontend hold the warehouse open.

## Acceptance note

Feature acceptance requires a real Docker smoke (SC-003). Shipping code + static tests alone is insufficient.
