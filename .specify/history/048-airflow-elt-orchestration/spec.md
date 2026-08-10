# Feature Specification: Airflow ELT Orchestration

**Feature Branch**: `feature/048-airflow-elt-orchestration`  
**Created**: 2026-08-09  
**Status**: Closed — accepted with verified Docker/Airflow smoke
**Input**: Spec 048 — Orquestación real del ELT con Apache Airflow

## Declaraciones de alcance (obligatorias)

- **Airflow es una capacidad técnica nueva** (orquestación académica/demo local).
- **`analytics/elt/pipelines/elt_pipeline.py` es la única implementación autoritativa** de transformaciones Medallion.
- **Airflow solo coordina**; no duplica transformaciones ni mueve DataFrames por XCom.
- **Ejecución inicial: manual** (`schedule=None`). Sin scheduling automático.
- **Entorno académico/demo local**, no HA ni producción.
- **DuckDB** sigue siendo el warehouse de negocio.
- **PostgreSQL de Airflow** solo metadata del orquestador.
- **Aplicación y rebuild Airflow NO deben escribir simultáneamente** el mismo DuckDB.
- **Sin** frontend ni endpoint FastAPI para disparar DAGs (aún).
- **Sin** Celery, Redis, Kubernetes, RBAC VOXMETRIKS, ni scheduling automático.
- **No se afirma soporte productivo.**

## User Scenarios & Testing

### User Story 1 — Orquestar Medallion por etapas reales (P1)

Como operador académico, detengo la demo de aplicación, levanto Airflow local, disparo `voxmetriks_elt` y veo en el graph cada etapa ejecutando trabajo real (Bronze→…→Validate→Finalize).

**Independent Test**: DAG parseable; cada task invoca `orchestrated_pipeline.py <stage>` contra data temporal.

**Acceptance Scenarios**:

1. **Given** Airflow up y data aislada con Bronze cache, **When** se dispara el DAG, **Then** las 8 tareas corren en orden y `verify_warehouse` pasa.
2. **Given** DuckDB bloqueado por la app, **When** `preflight`, **Then** falla con mensaje accionable (sin matar procesos ni borrar WAL/DB).

### User Story 2 — CLI por etapa sin Airflow (P1)

Como ingeniero, ejecuto cada etapa por CLI sobre un directorio temporal para depurar.

**Independent Test**: `python …/orchestrated_pipeline.py <stage>` exit codes correctos.

### User Story 3 — Compatibilidad del pipeline clásico (P2)

`python analytics/elt/pipelines/elt_pipeline.py` / `make pipeline` siguen funcionando.

## Edge Cases

- Bronze ausente y sin credenciales PocketBase → fallo en preflight/extract.
- Silver vacío → fallo en load_staging.
- `verify_warehouse` False → exit ≠ 0; no finalize.
- Fallo mid-DAG → tasks downstream no corren; no finalize exitoso.
- Doble DAG run → impedido por `max_active_runs=1`.

## Requirements

### Functional Requirements

- **FR-001**: Stack Airflow 3.3.0 + Python 3.12 bajo `infrastructure/airflow/` con LocalExecutor y Postgres metadata.
- **FR-002**: DAG `voxmetriks_elt` con etapas: preflight, extract_bronze, transform_silver, load_staging, build_gold_and_aggregates, export_gold, validate_warehouse, finalize_run.
- **FR-003**: Handoff durable vía Parquet/DuckDB; XCom solo metadata pequeña o deshabilitado.
- **FR-004**: `run_id` determinista INTEGER desde `dag_run_id`; original en `details`.
- **FR-005**: UI en `localhost:8081`; comandos `make airflow-*`.
- **FR-006**: Compose canónico root sigue siendo solo backend/frontend.
- **FR-007**: Tests y smokes usan data temporal; no mutar DuckDB canónico en CI de implementación.
- **FR-008**: Sin Redis/Celery; sin `_PIP_ADDITIONAL_REQUIREMENTS` dinámico; deps en imagen custom.

### Key Entities

- **DAG run**: identidad Airflow + `ctl_run_id` INTEGER.
- **Medallion artifacts**: Bronze/Silver/Gold Parquet + DuckDB warehouse.
- **Airflow metadata DB**: Postgres aislado.

## Success Criteria

- **SC-001 (código)**: DAG definido con APIs Airflow 3 (`airflow.sdk`, BashOperator del provider standard); etapas secuenciales reales vía adaptador.
- **SC-002 (estático)**: Gates backend/frontend verdes; compose YAML válido; tests Spec 048 sin skips.
- **SC-003 (runtime — aceptación)**: Smoke Docker real obligatorio: `compose config` → build → init → health → `dags list` sin import errors → ejecución DAG/`dags test` sobre data temporal → verify warehouse/ctl/exports → `down -v`.
- **SC-004**: Documentación distingue app compose vs Airflow compose vs CLI; no se afirma producción.
- **No basta** reportar runtime “no comprobado”: sin SC-003 el feature **no** está aceptado.
