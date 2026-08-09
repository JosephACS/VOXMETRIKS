# Contract: Airflow ↔ Canonical ELT Orchestration

**Spec**: 048  
**DAG id**: `voxmetriks_elt`  
**Adapter**: `analytics/elt/pipelines/orchestrated_pipeline.py`  
**Authority**: `analytics/elt/pipelines/elt_pipeline.py`

## Stage contract

| Order | Stage id | Canonical reuse | Durable inputs | Durable outputs | Failure semantics |
|------:|----------|-----------------|----------------|-----------------|-------------------|
| 1 | `preflight` | path/env + DuckDB probe | config/env | metadata JSON | non-zero exit; actionable lock message |
| 2 | `extract_bronze` | `PocketBaseClient`, `bronze_extract` | PB creds or cache | `bronze/raw_spotify.parquet` | RuntimeError |
| 3 | `transform_silver` | `silver_transform` | Bronze parquet | `silver/silver_spotify.parquet` | empty → fail |
| 4 | `load_staging` | `apply_schema`, `gold_load_staging` | Silver parquet | DuckDB `raw_spotify` | transactional; rollback on error |
| 5 | `build_gold_and_aggregates` | `gold_build_warehouse` | staging | dims/facts/aggs | transactional; no unrelated `app_*` edits |
| 6 | `export_gold` | `_export_gold_parquets` | Gold tables | `gold/*.parquet` | non-zero on error |
| 7 | `validate_warehouse` | `verify_warehouse` | warehouse | ctl stage row | **False → exit 2** |
| 8 | `finalize_run` | `_register_load`, `_audit`, `ctl_pipeline_stages` | prior OK stages | ctl success | refuses if prior failures/incomplete |

## Process boundary

- Airflow task → `python orchestrated_pipeline.py <stage> --dag-run-id <id>`
- No DataFrame XCom.
- `ctl_run_id = deterministic_hash(dag_run_id)` fitting INTEGER.
- `details` includes original `dag_run_id`.

## Runtime isolation

| System | Store |
|--------|-------|
| VOXMETRIKS warehouse | DuckDB via `DB_PATH` / `VOXMETRIKS_DATA_DIR` |
| Airflow metadata | Postgres service volume |

## Compatibility

- `run_pipeline()` and `make pipeline` remain supported end-to-end entrypoints.
- Root `compose.yml` remains backend+frontend only.
