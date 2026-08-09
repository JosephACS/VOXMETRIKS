# Tasks: Spec 048 — Airflow ELT Orchestration

## Phase A — Spec Kit
- [x] Open `.specify/features/048-airflow-elt-orchestration/`
- [x] Write spec/plan/research/data-model/quickstart/tasks/contracts
- [x] Set `.specify/feature.json` active → 048

## Phase B — Airflow stack
- [x] `infrastructure/airflow/compose.yml` LocalExecutor + Postgres, UI 8081
- [x] `AIRFLOW__CORE__EXECUTION_API_SERVER_URL` + `AIRFLOW__API__BASE_URL`
- [x] Dockerfile from `apache/airflow:3.3.0-python3.12` + pinned requirements + `pip check` + import probe
- [x] `.env.example` placeholders; `make airflow-up` refuses insecure placeholders
- [x] DAG `voxmetriks_elt.py` via `airflow.sdk` + standard BashOperator; `schedule=None`

## Phase C — Adapter
- [x] `orchestrated_pipeline.py` CLI stages + durable handoff
- [x] Exact six required stages before finalize; transactional load/build/finalize
- [x] Strict export for orchestrated path (`strict=True`); classic pipeline `strict=False`
- [x] Deterministic `ctl_run_id`; ImportError-only import fallback
- [x] Preserve `run_pipeline()` compatibility

## Phase D — Ops/Docs
- [x] Makefile `airflow-up|down|logs|list|trigger`
- [x] Update README/QUICKSTART/STATUS/elt/deployment + UML
- [x] Document DuckDB maintenance mode + Docker required for Airflow
- [x] Isolated CI workflow `.github/workflows/airflow-elt.yml` (not claimed green until run)

## Phase E — Gates
- [x] Validación estática (tests Spec 048, YAML, py_compile, docs, git diff --check)
- [ ] Runtime Docker/Airflow (compose config → build → init → health → dags list → smoke temporal → down -v) — **pendiente de evidencia real**
