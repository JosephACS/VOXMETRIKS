# Research: Spec 048 — Apache Airflow orchestration

**Date**: 2026-08-09  
**Sources (official)**:

- https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- https://airflow.apache.org/docs/docker-stack/build.html

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Version | Airflow **3.3.0** + Python **3.12** | Explicit pin required by Spec 048 |
| Executor | **LocalExecutor** | Academic/demo; avoids Redis/Celery |
| Metadata | **Postgres 16** service | Official compose pattern; not DuckDB |
| UI port | **8081** | Avoid clash with app ports |
| Custom image | `FROM apache/airflow:3.3.0-python3.12` + `pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt` | Official build practice; no `_PIP_ADDITIONAL_REQUIREMENTS` |
| Examples | Disabled (`LOAD_EXAMPLES=false`) | Spec requirement |
| Schedule | `None` + `catchup=False` | Manual only |
| Task I/O | Subprocess CLI + Parquet/DuckDB | No DataFrame XCom |
| Concurrency | `max_active_runs=1`, `max_active_tasks=1` | DuckDB single-writer |
| Services | postgres, airflow-init, api-server, scheduler, dag-processor | Minimal AF 3.3 set without Celery worker/redis |
| Public DAG APIs | `from airflow.sdk import DAG` + `airflow.providers.standard.operators.bash.BashOperator` | Airflow 3 public surface |
| Provider pins | `apache-airflow-providers-standard==1.15.0`, `apache-airflow-providers-fab==3.7.1` | From `constraints-3.3.0` / `constraints-3.12.txt` |
| Execution API | `AIRFLOW__CORE__EXECUTION_API_SERVER_URL=http://airflow-api-server:8080/execution/` | AF 3.3 task execution contract |
| External UI URL | `AIRFLOW__API__BASE_URL=http://localhost:8081` | Browser access via published port |
| Run identity | `VOXMETRIKS_DAG_RUN_ID` env (Jinja `{{ run_id }}`) — not shell-interpolated in `bash_command` | Safe quoting |

## Alternatives rejected

- CeleryExecutor + Redis: out of scope, heavier, not needed for LocalExecutor.
- Embedding Airflow in root `compose.yml`: would couple app runtime with long ELT rebuilds.
- Rewriting transforms inside DAG Python callables: violates “canonical ELT only”.
- Triggering rebuild while API is up: DuckDB lock risk; maintenance mode required.
- Legacy `airflow.operators.bash` / `airflow.models.DAG` as primary imports: prefer AF3 public SDK + standard provider.

## Risks

| Risk | Mitigation |
|------|------------|
| DuckDB lock | preflight fail-fast; docs: stop demo first |
| Docker unavailable on host | Static gates only; **acceptance blocked** until real smoke (SC-003) |
| Provider/image drift | Pin providers from official constraints; `pip check` + import probe in Dockerfile |
| Insecure demo secrets | `make airflow-up` refuses `replace-me` / weak JWT placeholders |