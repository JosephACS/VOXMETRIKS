# Data Model Notes — Spec 048

## Unchanged business warehouse (DuckDB)

Canonical path: `data/warehouse/voxmetrik.duckdb` (overridable via `DB_PATH` / `VOXMETRIKS_DATA_DIR`).

Medallion artifacts:

| Layer | Artifact |
|-------|----------|
| Bronze | `data/bronze/raw_spotify.parquet` |
| Silver | `data/silver/silver_spotify.parquet` |
| Gold export | `data/gold/*.parquet` |
| Control | `ctl_pipeline_stages`, `ctl_carga_dataset`, `ctl_auditoria` |

### `ctl_pipeline_stages.run_id`

- Type: **INTEGER** (existing DDL).
- Orchestrated runs: `ctl_run_id = sha256(dag_run_id)[:8] as int % (2^31-1)` (deterministic, >0).
- Original Airflow `dag_run_id` stored in `details`.

## Airflow metadata (PostgreSQL)

Separate database/volume (`voxmetriks-airflow-postgres`). Stores Airflow internal metadata only. **Must not** be presented as VOXMETRIKS warehouse.

## Non-goals

- No new fact/dim tables for orchestration.
- No mutation of unrelated `app_*` tables during Gold build.
