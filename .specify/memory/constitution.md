<!--
Sync Impact Report
==================
Version change: 0.0.0 (template) → 1.0.0 (ratified)
Modified principles: N/A — initial ratification from architectural audit (2026-06-19)
Added sections: All 24 enterprise sections (§1–§24) + Governance
Removed sections: Generic Spec Kit placeholder principles
Templates requiring updates:
  - .specify/templates/plan-template.md — ⚠ pending (Constitution Check references should align manually on first /speckit-plan)
  - .specify/templates/spec-template.md — ⚠ pending
  - .specify/templates/tasks-template.md — ⚠ pending
Deferred items: None
Ratification: Initial constitution derived from codebase audit; stakeholder formal sign-off TODO if required by org policy
-->

# Constitución Empresarial de Voxmetriks

**Documento:** Constitución del Proyecto Voxmetriks  
**Metodología:** GitHub Spec Kit (Spec-Driven Development)  
**Alcance:** Repositorio `voxmetriks` — plataforma de streaming musical y analítica de datos  
**Autoridad:** Este documento prevalece sobre documentación legacy, specs Kiro no ratificadas y decisiones ad hoc no registradas en Specify.

**Version**: 1.0.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-06-19

---

## Tabla de Contenidos

1. [Propósito del Proyecto](#1-propósito-del-proyecto)
2. [Visión Empresarial](#2-visión-empresarial)
3. [Alcance del Sistema](#3-alcance-del-sistema)
4. [Niveles Empresariales](#4-niveles-empresariales)
5. [Principios Arquitectónicos](#5-principios-arquitectónicos)
6. [Arquitectura Oficial del Sistema](#6-arquitectura-oficial-del-sistema)
7. [Estándares Tecnológicos](#7-estándares-tecnológicos)
8. [Estrategia de Datos](#8-estrategia-de-datos)
9. [Estrategia de Calidad](#9-estrategia-de-calidad)
10. [Estrategia de Testing](#10-estrategia-de-testing)
11. [Estándares de Documentación](#11-estándares-de-documentación)
12. [Trazabilidad Empresarial](#12-trazabilidad-empresarial)
13. [Organización Oficial del Repositorio](#13-organización-oficial-del-repositorio)
14. [Convenciones de Nomenclatura](#14-convenciones-de-nomenclatura)
15. [Reglas para Especificaciones Futuras](#15-reglas-para-especificaciones-futuras)
16. [Reglas para Implementación](#16-reglas-para-implementación)
17. [Reglas para UML](#17-reglas-para-uml)
18. [Reglas para Seguridad](#18-reglas-para-seguridad)
19. [Reglas para APIs](#19-reglas-para-apis)
20. [Reglas para Data Warehouse](#20-reglas-para-data-warehouse)
21. [Reglas para ETL](#21-reglas-para-etl)
22. [Criterios de Aceptación Globales del Proyecto](#22-criterios-de-aceptación-globales-del-proyecto)
23. [Restricciones del Proyecto](#23-restricciones-del-proyecto)
24. [Glosario Empresarial de Voxmetriks](#24-glosario-empresarial-de-voxmetriks)

---

## 1. Propósito del Proyecto

Voxmetriks es una **plataforma empresarial de inteligencia musical** que integra experiencia de usuario tipo streaming con capacidades analíticas sobre catálogos musicales estilo Spotify. El propósito verificable del sistema, según la evidencia del código y los artefactos de gobernanza existentes, es:

1. **Ingerir** datasets de catálogo musical (CSV vía PocketBase, Parquet local o bootstrap sintético controlado).
2. **Transformar** esos datos mediante un pipeline ELT con arquitectura Medallion (Bronze → Silver → Gold) hacia un data warehouse analítico en DuckDB.
3. **Exponer** el catálogo, las métricas analíticas y las funcionalidades de usuario (playlists, favoritos, recomendaciones, perfil) mediante una API REST FastAPI con prefijo `/api/v1`.
4. **Presentar** una interfaz web Angular que unifique navegación de catálogo, reproductor musical, dashboards analíticos y herramientas de data engineering (pipeline ELT, explorador de warehouse).

Voxmetriks **no es** un servicio de streaming de audio en producción: el reproductor frontend utiliza assets WAV de demostración. El valor empresarial reside en **catálogo musical gobernado, analítica accionable, trazabilidad de pipeline y personalización de usuario** sobre un warehouse unificado.

El propósito de evolución del proyecto, documentado en `.kiro/specs/voxmetrik-professionalization/requirements.md` y ratificado aquí, es **professionalizar el sistema existente sin reescritura arquitectónica**: mejorar documentación, estabilizar infraestructura, establecer pruebas, observabilidad y gobernanza SDD — preservando FastAPI, DuckDB, Angular y el pipeline ELT como pilares inmutables salvo enmienda constitucional.

---

## 2. Visión Empresarial

### 2.1 Visión (horizonte 3–5 años)

Voxmetriks será la **plataforma de referencia interna** para equipos que necesiten combinar experiencia de consumo musical con analítica de datos de catálogo, comportamiento simulado y métricas de engagement — gobernada por especificaciones trazables, datos auditables y arquitectura medallion reproducible en contenedores.

### 2.2 Misión operativa

Entregar un ecosistema software donde:

- Los **analistas de datos** exploten un warehouse dimensional con hechos, agregados y capa enterprise documentada.
- Los **desarrolladores** evolucionen features bajo Spec-Driven Development con constitución, specs, planes y tareas versionados en Git.
- Los **usuarios finales** interactúen con catálogo, playlists, favoritos y recomendaciones sobre datos gobernados.
- Los **ingenieros de datos** operen pipelines ELT observables con tablas de control (`ctl_*`) y validación post-carga.

### 2.3 Propuesta de valor diferenciada

| Dimensión | Voxmetriks | Justificación (evidencia) |
|-----------|------------|---------------------------|
| **Unificación UX + Analytics** | SPA Angular con módulos streaming y analytics en un solo shell | 18 rutas lazy-loaded, `StatsService` con 15+ métodos |
| **Warehouse embebido de alto rendimiento** | DuckDB OLAP en archivo único | 35+ tablas, queries analíticas sin cluster externo |
| **Pipeline resiliente** | Fallbacks PocketBase → Parquet → bootstrap | `elt/pipelines/elt_pipeline.py` |
| **Extensibilidad enterprise** | Capa synthetic behavioral + agregados | `enterprise_analytics.py`, ~220k filas fact sintéticas |
| **Gobernanza SDD** | Spec Kit + trazabilidad Git | `.specify/`, skills `/speckit-*` |

### 2.4 Alineación estratégica

La visión se materializa en tres outcomes medibles:

1. **Time-to-insight:** desde ingesta CSV hasta dashboard analytics en un solo entorno Docker o dev local.
2. **Time-to-feature:** nueva capacidad siguiendo flujo Constitution → Specify → Plan → Tasks → Implement con gates de calidad.
3. **Auditability:** toda carga ELT y mutación crítica de catálogo deja rastro en tablas de control o commits Git trazables a specs.

---

## 3. Alcance del Sistema

### 3.1 Dentro del alcance (In Scope)

| Dominio | Capacidades incluidas |
|---------|----------------------|
| **Ingesta** | PocketBase colección `datasets`, CSV/Parquet, bootstrap catalog |
| **ELT** | Pipeline medallion, capa enterprise, export Gold Parquet |
| **Warehouse** | Modelo dimensional + facts enterprise + agregados + tablas `app_*` |
| **API** | 54 endpoints: catálogo CRUD, stats, analytics, users, playlists, favorites |
| **Frontend** | Auth, catálogo, player demo, analytics, recommendations, ELT UI, explorer |
| **Contenedores** | Docker Compose: pipeline job, API, PocketBase |
| **Gobernanza** | Constitución, specs Specify, OpenAPI auto-generada |
| **Professionalización** | Docs, CI (tests+lint), observabilidad, estabilización Docker |

### 3.2 Fuera del alcance (Out of Scope)

Ratificado desde Kiro requirements y evidencia de código:

| Exclusión | Razón |
|-----------|-------|
| Reescritura completa del backend o frontend | Principio "evolucionar, no reescribir" |
| Reemplazo de FastAPI, DuckDB o Angular | Stack inmutable salvo enmienda |
| Recreación del pipeline ELT desde cero | Pipeline funcional en `elt/` |
| Modificación masiva del esquema warehouse existente sin spec | Riesgo de ruptura analítica |
| Streaming de audio real / CDN / DRM | Player usa demo WAV; no hay backend streaming |
| CD completo automatizado (inicialmente) | Kiro: CI only en fase 1 |
| Autenticación OAuth/JWT externa (fase actual) | Implementación actual: tokens opacos en DuckDB |
| PocketBase como auth provider del API | Configurado pero no implementado |

### 3.3 Límites del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTERA DE VOXMETRIKS                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Angular SPA │◄─┤ FastAPI API │◄─┤ DuckDB Warehouse    │  │
│  └─────────────┘  └──────┬──────┘  └──────────▲──────────┘  │
│                          │                      │              │
│                   PocketBase (opcional)        ELT Pipeline    │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │ Fuera: Spotify API real      │ Fuera: Kafka, Spark,
         │ Fuera: Pagos / suscripciones │        Snowflake, K8s prod
```

---

## 4. Niveles Empresariales

Voxmetriks opera en tres niveles empresariales interconectados. Cada decisión arquitectónica MUST mapearse al menos a un nivel.

### 4.1 Nivel Estratégico

**Horizonte:** visión, objetivos de negocio, outcomes, restricciones de evolución.

| Elemento | Artefacto canónico | Estado actual |
|----------|-------------------|---------------|
| Visión y propuesta de valor | Esta Constitución §2 | Ratificado |
| Diagrama casos de uso general | `README.md` (imagen UC) | Existe; complementar con texto |
| Objetivo professionalización | `.kiro/specs/.../requirements.md` | Referencia histórica; Specify prevalece |
| Principio "no reescritura" | Constitución §5, §23 | Ratificado |

**Responsabilidad:** definir *por qué* existe Voxmetriks y qué NO debe cambiar sin enmienda.

### 4.2 Nivel Táctico

**Horizonte:** arquitectura, diseño de dominios, topología de despliegue, estándares.

| Elemento | Artefacto canónico | Estado actual |
|----------|-------------------|---------------|
| Arquitectura de capas | Constitución §6 | Ratificado |
| Package-by-domain | `apps/backend/app/packages/`, `frontend/src/app/packages/` | Implementado |
| Topología Docker | `infrastructure/docker/docker-compose.yml` | Compose alineado; Dockerfile pendiente fix |
| Modelo de datos warehouse | `elt/pipelines/elt_pipeline.py`, `enterprise_analytics.py` | Implementado |
| Workflow SDD | `.specify/workflows/speckit/workflow.yml` | Instalado |
| Diseño target Kiro | `.kiro/specs/.../design.md` | Referencia; validar vs código |

**Responsabilidad:** definir *cómo* se estructura el sistema y cómo evolucionan dominios.

### 4.3 Nivel Operativo

**Horizonte:** ejecución, runbooks, scripts, health checks, pipeline runs.

| Elemento | Artefacto canónico | Estado actual |
|----------|-------------------|---------------|
| Dev local Windows | `scripts/dev_start.bat` | **Fuente operativa más fiable** |
| Pipeline ELT | `python analytics/elt/pipelines/elt_pipeline.py` | Entry point canónico |
| Validación warehouse | `scripts/validate_warehouse.py` | Disponible |
| Health API | `GET /health` | Implementado |
| Control ELT | `ctl_carga_dataset`, `ctl_auditoria`, `ctl_pipeline_stages` | Implementado |
| Configuración | `.env` (no versionado), `.env.example` | Compartido pipeline+API |
| Quickstarts legacy | `quickstart.md`, `docs/*` | **Desactualizados — no usar como runbook** |

**Responsabilidad:** definir *cómo se ejecuta* el sistema día a día.

### 4.4 Matriz de correspondencia

| Decisión | Estratégico | Táctico | Operativo |
|----------|:-----------:|:-------:|:---------:|
| Mantener DuckDB | ✓ | ✓ | ✓ |
| Medallion Bronze/Silver/Gold | ✓ | ✓ | ✓ |
| 54 endpoints API | | ✓ | ✓ |
| `dev_start.bat` como orquestador dev | | | ✓ |
| Spec Kit SDD workflow | ✓ | ✓ | ✓ |
| Etiquetado datos sintéticos | ✓ | ✓ | ✓ |

---

## 5. Principios Arquitectónicos

Todo cambio MUST evaluarse contra estos principios. Un PR que viole un principio MUST incluir justificación explícita y plan de remediación en la spec asociada.

### P1. Evolución sobre Reescritura

**Declaración:** El sistema existente es un activo funcional. Las mejoras MUST ser incrementales sobre la base de código actual.

**Justificación:** Kiro requirements explicita out-of-scope "complete backend rewrite". El backend expone 54 endpoints funcionales; el frontend tiene 42 componentes y 18 rutas. Reescribir implica riesgo desproporcionado sin beneficio demostrado.

**Implicaciones:**
- Refactors MUST preservar contratos API públicos salvo spec de breaking change.
- Migraciones de esquema MUST ser idempotentes (`IF NOT EXISTS`, `ALTER IF NOT EXISTS`).
- Documentación legacy se archiva, no se usa como base de reimplementación.

### P2. Package-by-Domain (Backend y Frontend)

**Declaración:** La organización del código MUST seguir dominios de negocio alineados entre capas.

**Dominios oficiales:**

| Dominio | Backend | Frontend |
|---------|---------|----------|
| Streaming | `packages/streaming/` | `packages/streaming/` |
| Analytics | `packages/analytics/` | `packages/analytics/` |
| Users | `packages/users/` | `packages/users/` |
| Data Engineering | (API analytics/stats) | `packages/data-engineering/` |
| Recommendations | (API analytics) | `packages/recommendations/` |
| History | (API analytics/history) | `packages/history/` |
| Administration | — | `packages/administration/` |

**Justificación:** Evidencia en `apps/backend/app/packages/` y `frontend/src/app/packages/`. Nuevas features MUST ubicarse en el dominio correspondiente o crear dominio nuevo con spec que lo justifique.

### P3. Medallion Data Architecture

**Declaración:** Toda ingesta de datos MUST fluir por capas Bronze → Silver → Gold antes de consumo analítico.

**Justificación:** Implementado en `elt/pipelines/elt_pipeline.py` con directorios `data/bronze/`, `data/silver/`, `data/gold/` y carga final a DuckDB.

**Implicaciones:**
- No se permite carga directa a tablas dimensionales sin pasar por staging documentado.
- Cada ejecución MUST registrar estado en tablas `ctl_*`.

### P4. Single Warehouse Authority

**Declaración:** La fuente analítica canónica es un único archivo DuckDB en ruta resuelta por `apps/backend/app/core/config.py`.

**Ruta canónica:** `{project_root}/data/warehouse/voxmetrik.duckdb`

**Justificación:** `config.py` resuelve buscando `data/warehouse/` en ancestros del proyecto. Rutas legacy (`duckdb/`, `/app/duckdb/`) MUST desaparecer de configs activos.

### P5. Schema Introspection over Assumption

**Declaración:** El backend MUST NOT asumir columnas de tablas DuckDB. Los servicios MUST usar `get_table_columns()`, `table_exists()` y `safe_query()` de `app/core/database.py`.

**Justificación:** El warehouse evolucionó (enterprise layer, ALTER columns). Servicios ya implementan este patrón defensivo.

### P6. Separation: Warehouse Data vs Application Data

**Declaración:**
- **Warehouse (`dim_*`, `fact_*`, `agg_*`, `raw_*`, `ctl_*`):** poblado por ELT; lectura principal para analytics.
- **Application (`app_*`):** poblado por API en startup/mutaciones; estado de sesión, playlists, favoritos.

**Justificación:** `user_storage.py` y `app_storage.py` crean `app_*` en runtime; pipeline crea warehouse tables.

### P7. ELT-before-API

**Declaración:** La API MUST validar existencia del warehouse en startup. Endpoints analíticos MUST degradar gracefully si faltan agregados, pero `/health` MUST reportar estado real.

**Justificación:** `main.py` lifespan verifica DB; servicios analytics tienen fallbacks documentados en código.

### P8. Spec-Driven Development (SDD)

**Declaración:** Toda feature no trivial MUST seguir el flujo Specify: Constitution → Specify → [Clarify] → [Checklist] → Plan → Tasks → [Analyze] → Implement.

**Justificación:** Spec Kit v0.11.3 instalado con integración `cursor-agent`. Skills en `.cursor/skills/speckit-*`.

### P9. Contract-First API

**Declaración:** La OpenAPI generada en `/docs` es la referencia de contrato API. Pydantic models en `app/shared/schemas/models.py` y `frontend/shared/models/api.models.ts` MUST mantenerse alineados.

**Justificación:** 54 endpoints con validación Pydantic; frontend tipado con 514 líneas de DTOs.

### P10. Explicit Synthetic Data Boundary

**Declaración:** Datos generados por `enterprise_analytics.py` y endpoints como `POST /api/v1/stats/synthetic` MUST identificarse como **synthetic** en specs, respuestas API (metadata cuando aplique) y documentación.

**Justificación:** ~220k filas de streaming sintético mezcladas con catálogo real crean riesgo de interpretación incorrecta en analytics.

### P11. Security-by-Default for Mutations (Target State)

**Declaración:** Endpoints que mutan catálogo warehouse, generan datos sintéticos masivos o exponen explorer MUST requerir autenticación y autorización. El estado actual (CRUD catálogo sin auth) es **deuda conocida** con remediación obligatoria priorizada.

**Justificación:** Auditoría identificó POST synthetic sin auth, CORS `*`, SHA-256 sin salt.

### P12. Observability as First-Class (Target State)

**Declaración:** Logging estructurado, request correlation IDs y métricas de pipeline MUST implementarse según backlog Kiro Phase 1. `python-json-logger` en deps MUST utilizarse.

**Justificación:** Logging actual es `basicConfig`; Kiro tasks 1.1.x–1.2.x planifican structured JSON.

---

## 6. Arquitectura Oficial del Sistema

### 6.1 Estilo arquitectónico

**Modular Monolith** en backend (FastAPI) + **SPA** en frontend (Angular) + **Embedded OLAP Warehouse** (DuckDB) + **Batch ELT Pipeline**.

No hay microservicios. La separación lógica es por packages de dominio, no por despliegue independiente.

### 6.2 Diagrama de contenedores (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Usuario / Analista                              │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTPS
                    ┌─────────────▼─────────────┐
                    │   Angular SPA (:4200)     │
                    │   Standalone + Signals    │
                    │   packages/* domains      │
                    └─────────────┬─────────────┘
                                  │ REST /api/v1
                    ┌─────────────▼─────────────┐
                    │   FastAPI (:8000)         │
                    │   app/packages/*          │
                    │   routes → services → SQL │
                    └─────────────┬─────────────┘
                                  │ DuckDB SQL
                    ┌─────────────▼─────────────┐
                    │   DuckDB Warehouse        │
                    │   voxmetrik.duckdb        │
                    │   dim_*/fact_*/agg_*/app_*│
                    └─────────────▲─────────────┘
                                  │ ELT Load
                    ┌─────────────┴─────────────┐
                    │   ELT Pipeline (batch)    │
                    │   elt/pipelines/          │
                    │   Bronze→Silver→Gold     │
                    └─────────────▲─────────────┘
                                  │ CSV
                    ┌─────────────┴─────────────┐
                    │   PocketBase (:8090)      │
                    │   collection: datasets    │
                    └───────────────────────────┘
```

### 6.3 Capas internas del backend

```
┌─────────────────────────────────────────┐
│  Routes (HTTP handlers, thin)           │  packages/*/routes/
├─────────────────────────────────────────┤
│  Services (business logic, SQL)         │  packages/*/services/
├─────────────────────────────────────────┤
│  Shared Schemas (Pydantic DTOs)         │  app/shared/schemas/
├─────────────────────────────────────────┤
│  Core (config, database, logging)       │  app/core/
└─────────────────────────────────────────┘
         │
         ▼
    DuckDB (no ORM)
```

**Regla:** No se introduce capa Controller separada. Routes invocan Services directamente.

### 6.4 Capas internas del frontend

```
┌─────────────────────────────────────────┐
│  Pages / Feature Components             │  packages/*/
├─────────────────────────────────────────┤
│  Shared Components + Pipes              │  shared/components/
├─────────────────────────────────────────┤
│  Domain Services (HttpClient)           │  packages/*/services/, core/
├─────────────────────────────────────────┤
│  Guards + Interceptors                  │  core/guards/, core/interceptors/
├─────────────────────────────────────────┤
│  Models (DTOs)                          │  shared/models/api.models.ts
└─────────────────────────────────────────┘
```

### 6.5 Flujo de datos end-to-end

```
PocketBase CSV ──► Bronze Parquet ──► Silver Parquet ──► Gold DuckDB + Gold Parquet
                                                              │
                                                              ├──► Analytics API
                                                              ├──► Explorer API
                                                              └──► Catalog CRUD API
                                                                       │
User Actions ──► app_* tables ◄──────────────────────────────────────┘
(playlists, favorites, sessions)
```

### 6.6 Dependencias entre componentes

| Componente | Depende de | Contrato |
|------------|------------|----------|
| Frontend | FastAPI `/api/v1` | OpenAPI + `api.models.ts` |
| FastAPI analytics | Warehouse `agg_*`, `fact_*` | SQL + schema introspection |
| FastAPI streaming CRUD | Warehouse `dim_*` | SQL parametrizado |
| FastAPI user features | `app_*` tables | Auth Bearer token |
| ELT Pipeline | PocketBase o Parquet o bootstrap | `.env`, `PB_COLLECTION=datasets` |
| Docker API | Pipeline exit 0 + volume duckdb | `depends_on: service_completed_successfully` |

---

## 7. Estándares Tecnológicos

### 7.1 Frontend

| Atributo | Estándar | Versión pin (evidencia) |
|----------|----------|-------------------------|
| Framework | Angular standalone components | `^21.2.0` (`package.json`) |
| State | Signals + RxJS Observables | Angular 21 signals-first |
| Routing | Lazy `loadComponent()` | `app.routes.ts` |
| HTTP | `HttpClient` + `withFetch()` | `app.config.ts` |
| i18n | Custom `I18nService` + `TranslatePipe` | ES/EN |
| Testing | Vitest via `@angular/build:unit-test` | vitest `^4.0.8` |
| Linting/format | Prettier | `^3.8.1` |
| UI libraries | **Prohibido** introducir Material/PrimeNG sin spec | Custom CSS design system |
| TypeScript | strict mode | `tsconfig.json` |

**Reglas:**
- MUST NOT usar NgModules en código nuevo.
- MUST lazy-load feature routes.
- MUST tipar respuestas API con `api.models.ts`.
- `environment.prod.ts` MUST configurarse con URL API de producción antes de deploy (actualmente apunta a localhost — deuda).

### 7.2 Backend

| Atributo | Estándar | Versión pin |
|----------|----------|-------------|
| Framework | FastAPI | `0.111.0` (`backend/requirements.txt`) |
| Server | Uvicorn | `0.30.1` |
| Validation | Pydantic v2 | `2.7.4` |
| Config | pydantic-settings | `2.3.4` |
| Database driver | duckdb | `1.1.3` |
| Python | 3.12 | **Prohibido 3.13+** (compat wheels) |
| Entry point | `apps/backend/app/main.py` | `uvicorn app.main:app` desde `apps/backend/` |
| Pattern | routes → services → SQL | Sin ORM |

**Reglas:**
- MUST NOT compilar dependencias desde fuente (wheels prebuilt only).
- MUST usar `backend/requirements.txt` como única fuente de dependencias Python (API + ELT + tests).
- MUST usar `get_conn()` / `get_write_conn()` para acceso DuckDB.

### 7.3 Datos

| Atributo | Estándar |
|----------|----------|
| Warehouse engine | DuckDB 1.1.3 |
| Processing | Pandas 2.2.2, PyArrow 16.1.0 |
| Formato intermedio | Parquet |
| Modelo | Star schema + enterprise extensions |
| DDL authority | `elt/pipelines/elt_pipeline.py` + `elt/transform/enterprise_analytics.py` |
| Legacy DDL | `archive/legacy/schema.sql` — **NO autoritativo**; DDL canónico en ELT |
| Datos versionados | **Prohibido** commitear `.duckdb`, `.parquet`, `.csv` (`.gitignore`) |

### 7.4 Infraestructura

| Atributo | Estándar |
|----------|----------|
| Dev orchestration | `scripts/dev_start.bat` (Windows), equivalente shell para Unix |
| Config | `.env` (local, gitignored), `.env.example` (template) |
| Git hooks | `.githooks/commit-msg` |
| Spec Kit CLI | specify-cli 0.11.3, integración cursor-agent |
| CI (target) | GitHub Actions: pytest + lint (Kiro Phase 1) |

### 7.5 Contenedores

| Atributo | Estándar |
|----------|----------|
| Base image | `python:3.12-slim` |
| Compose services | `pipeline`, `api`, `pocketbase` |
| Pipeline command | `python analytics/elt/pipelines/elt_pipeline.py` |
| API command | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| DB volume | `duckdb_data:/app/data/warehouse` |
| PocketBase image | `spectado/pocketbase:latest` |

**Deuda Docker (MUST remediar):** Dockerfile MUST copiar directorio `elt/` completo, eliminar referencia a `elt_pipeline.py` in raíz, alinear `DB_PATH` y `CMD` con compose.

---

## 8. Estrategia de Datos

### 8.1 Bronze (Raw Landing)

**Ubicación:** `data/bronze/raw_spotify.parquet`

**Contenido:** Extract sin transformación significativa desde:
1. PocketBase CSV (primario)
2. Parquet local existente (fallback)
3. `bootstrap_catalog.py` — 8.500 tracks sintéticos (último fallback)

**Reglas:**
- Bronze MUST preservar datos fuente para reprocesamiento.
- MUST registrar modo de ingesta en `ctl_carga_dataset`.

### 8.2 Silver (Cleaned / Conformed)

**Ubicación:** `data/silver/silver_spotify.parquet`

**Transformaciones obligatorias:**
- Renombrado de columnas según mapa del pipeline
- Coerción de tipos
- Deduplicación por `track_id`
- Eliminación de filas con `track_name` nulo

**Reglas:**
- Silver es la entrada única autorizada para construcción de dimensiones Gold.

### 8.3 Gold (Curated / Analytics-Ready)

**Ubicación dual:**
- DuckDB: `data/warehouse/voxmetrik.duckdb`
- Export Parquet: `data/gold/*.parquet`

**Contenido:**
- Staging: `raw_spotify`
- Dimensiones: `dim_artista`, `dim_genero`, `dim_album`, `dim_track`, `dim_usuario`, `dim_playlist`, `dim_tiempo`
- Hechos: `fact_streaming` (+ columnas enterprise)
- Agregados: 15+ tablas `agg_*`
- Enterprise facts: `fact_user_activity`, `fact_searches`, `fact_stream_sessions`, etc.
- Control: `ctl_carga_dataset`, `ctl_auditoria`, `ctl_pipeline_stages`

**Capa Enterprise (`enterprise_analytics.py`):**
- Genera datos de comportamiento **sintéticos** para demos analíticos
- MUST etiquetarse como synthetic en toda documentación consumidor

### 8.4 Application Layer (`app_*`)

Creada en runtime por API, separada del pipeline:

| Tabla | Propósito |
|-------|-----------|
| `app_user` | Credenciales, plan, preferencias |
| `app_session` | Tokens de sesión |
| `app_playlist` | Playlists usuario |
| `app_playlist_track` | Tracks en playlist |
| `app_favorite` | Favoritos |

### 8.5 Política de calidad de datos

| Regla | Descripción |
|-------|-------------|
| Idempotencia | Pipeline MUST ser re-ejecutable sin corrupción |
| Auditoría | Toda carga MUST escribir en `ctl_*` |
| Validación post-ELT | `scripts/validate_warehouse.py` MUST ejecutarse tras pipeline en CI |
| Provenance | Responses analytics SHOULD incluir metadata de fuente (real/synthetic) cuando mezclen capas |
| No silent schema drift | Cambios DDL MUST actualizar pipeline Python, no solo `archive/legacy/schema.sql` |

---

## 9. Estrategia de Calidad

### 9.1 Dimensiones de calidad

| Dimensión | Definición Voxmetriks | Mecanismo |
|-----------|----------------------|-----------|
| **Funcional** | Endpoints y UI cumplen specs | Tests + manual QA + `/speckit-analyze` |
| **Datos** | Warehouse consistente post-ELT | `validate_warehouse.py`, `ctl_*` |
| **Contrato** | API ↔ Frontend alineados | OpenAPI + `api.models.ts` diff |
| **Seguridad** | Auth en mutaciones sensibles | Auth deps + future RBAC |
| **Mantenibilidad** | Package-by-domain, no dead code | Code review + lint |
| **Observabilidad** | Trazabilidad requests y pipeline | Structured logging (target) |

### 9.2 Gates de calidad SDD

Flujo obligatorio para features de producción:

```
/speckit-specify → /speckit-clarify → /speckit-checklist → /speckit-plan
    → /speckit-tasks → /speckit-analyze → /speckit-implement
```

`/speckit-analyze` MUST ejecutarse **antes** de implement si hay ambigüedad material.

### 9.3 Definition of Done (feature)

Una feature está DONE cuando:

1. Spec, plan y tasks están en `specs/NNN-feature/` y committed.
2. Implementación cumple criterios de aceptación de la spec.
3. Tests nuevos pasan (cuando aplique §10).
4. OpenAPI refleja cambios API.
5. No introduce regresiones en `/health`.
6. Constitution Check en plan.md está marcado PASS.
7. PR referencia spec directory y branch `NNN-feature-name`.

### 9.4 Deuda técnica conocida (registro obligatorio)

| ID | Deuda | Prioridad | Remediación |
|----|-------|-----------|-------------|
| TD-001 | Tests backend obsoletos | Alta | Reescribir contra `app.main:app`, `/api/v1` |
| TD-002 | Dockerfile desalineado | Alta | Copiar `elt/`, fix CMD/DB_PATH |
| TD-003 | CRUD catálogo sin auth | Alta | Spec security-hardening |
| TD-004 | SHA-256 passwords | Alta | bcrypt/argon2 migration spec |
| TD-005 | Docs legacy paths | Media | Spec documentation-reconciliation |
| TD-006 | `archive/legacy/schema.sql` stale | Media | Archivado |
| TD-007 | Historial solo localStorage | Media | Integrar `/analytics/history` |
| TD-008 | Dual requirements.txt | — | **Cerrado** — solo `backend/requirements.txt` |
| TD-009 | Frontend prod env localhost | Media | Config deploy spec |
| TD-010 | CORS `*` | Alta | Environment-specific origins |

---

## 10. Estrategia de Testing

### 10.1 Pirámide de pruebas target

```
        ┌─────────┐
        │  E2E    │  (futuro — smoke Docker compose)
       ┌┴─────────┴┐
       │ Integration│  Pipeline→Warehouse→API health
      ┌┴────────────┴┐
      │  Unit/Service │  pytest services, Vitest services
     ┌┴──────────────┴┐
     │  Contract       │  OpenAPI schema validation
     └─────────────────┘
```

### 10.2 Backend

| Tipo | Framework | Alcance mínimo target |
|------|-----------|----------------------|
| API integration | pytest + FastAPI TestClient | `/health`, CRUD artists/tracks, auth flow |
| Service unit | pytest | SQL services con DuckDB in-memory o test file |
| Pipeline smoke | pytest/script | `run_pipeline()` dry-run o post-run counts |

**Estado actual:** `apps/backend/tests/test_api.py` incompatible — MUST reescribirse antes de expandir coverage.

**Regla:** pytest MUST añadirse a `backend/requirements.txt` o grupo dev documentado.

### 10.3 Frontend

| Tipo | Framework | Alcance mínimo target |
|------|-----------|----------------------|
| Component | Vitest | AuthService, TracksService, StatsService |
| Guard | Vitest | authGuard, guestGuard |
| Smoke | Vitest | App bootstrap |

**Estado actual:** 1 spec (`app.spec.ts`) con assertion drift — MUST corregirse.

### 10.4 CI (target — Kiro Phase 1)

```yaml
# Target pipeline (no implementado aún)
- pip install -r backend/requirements.txt
- pytest apps/backend/tests/
- cd apps/frontend && npm test
- ruff/flake8 backend (cuando se adopte)
```

### 10.5 Reglas

- MUST NOT merge features que rompan tests existentes (cuando estén verdes).
- MUST añadir test por cada nuevo endpoint público.
- MUST añadir test por cada guard/interceptor de seguridad nuevo.
- Synthetic data generation endpoints MUST tener tests de autorización (cuando se añada auth).

---

## 11. Estándares de Documentación

### 11.1 Jerarquía de autoridad documental

| Prioridad | Fuente | Uso |
|:---------:|--------|-----|
| 1 | **Esta Constitución** | Principios, restricciones, gobernanza |
| 2 | **`specs/NNN-feature/`** (Specify) | Requisitos activos por feature |
| 3 | **OpenAPI `/docs`** | Contrato API runtime |
| 4 | **Código fuente** (`elt/`, `apps/backend/`, `apps/frontend/`) | Comportamiento real |
| 5 | **`.specify/templates/`** | Formatos SDD |
| 6 | **`.kiro/specs/`** | Referencia histórica — NO activa sin migración |
| 7 | **`docs/`, `quickstart.md`** | Legacy — archivar o regenerar |

### 11.2 Documentos obligatorios por feature (Specify)

```
specs/NNN-feature-name/
├── spec.md           # Requisitos, user stories, acceptance scenarios
├── plan.md           # Decisiones técnicas, Constitution Check
├── tasks.md          # Tareas accionables
├── checklists/       # Quality gates (opcional pero recomendado)
├── research.md       # Investigación (si aplica)
├── data-model.md     # Entidades afectadas (si aplica)
└── contracts/        # OpenAPI fragments, SQL contracts (si aplica)
```

### 11.3 Reglas de escritura

- MUST escribir en español o inglés consistente por documento (no mezclar en mismo archivo).
- MUST usar terminología del Glosario §24.
- MUST referenciar rutas canónicas, no paths legacy.
- MUST marcar datos synthetic explícitamente.
- MUST incluir fecha y versión en specs.

### 11.4 Migración Kiro → Specify

- Contenido de `.kiro/specs/voxmetrik-professionalization/` MAY usarse como input para specs Specify.
- MUST NOT mantener dos sistemas activos para la misma feature.
- Tras migración, Kiro spec MUST marcarse "superseded by specs/NNN-*".

---

## 12. Trazabilidad Empresarial

### 12.1 Cadena de trazabilidad oficial

Voxmetriks adopta la siguiente cadena obligatoria para features empresariales:

```
OE → OT → OO → Meta → Departamento → Paquete → Caso de Uso → Historia de Usuario
  → Especificación → Implementación
```

### 12.2 Definición de eslabones

| Eslabón | Código | Descripción | Artefacto Specify/Git |
|---------|--------|-------------|----------------------|
| Objetivo Estratégico | **OE** | Meta de negocio de alto nivel | Constitución §2, roadmap |
| Objetivo Táctico | **OT** | Iniciativa que contribuye a OE | `spec.md` sección Strategic Alignment |
| Objetivo Operativo | **OO** | Resultado medible entregable | `spec.md` Success Metrics |
| Meta | **Meta** | KPI cuantificable | `spec.md` Acceptance Criteria |
| Departamento | **Departamento** | Área responsable (Data, Platform, UX) | `plan.md` Ownership |
| Paquete | **Paquete** | Dominio código (`streaming`, `analytics`, etc.) | `plan.md` Project Structure |
| Caso de Uso | **CU** | Interacción actor-sistema | `spec.md` User Scenarios |
| Historia de Usuario | **HU** | "Como [rol], quiero [acción], para [beneficio]" | `spec.md` User Stories P1/P2/P3 |
| Especificación | **Spec** | Documento formal de requisitos | `specs/NNN-*/spec.md` |
| Implementación | **Impl** | Código + tests + commits | Branch `NNN-*`, PRs |

### 12.3 Matriz de trazabilidad (plantilla)

Cada `spec.md` MUST incluir tabla:

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-01 | OO-01 | M-01 | Data | analytics | CU-01 | US-01 | spec.md | PR #N |

### 12.4 Trazabilidad técnica Git

| Elemento | Convención |
|----------|------------|
| Branch | `NNN-feature-short-name` (Specify sequential) |
| Spec directory | `specs/NNN-feature-short-name/` |
| Commit message | Referenciar spec: `feat(analytics): implement trending filter (automation/specs/003-trending-filters)` |
| PR description | Link a spec.md + plan.md + tasks completados |

### 12.5 Trazabilidad de datos (ELT)

| Evento | Registro |
|--------|----------|
| Pipeline run | `ctl_carga_dataset`, `ctl_pipeline_stages` |
| Auditoría | `ctl_auditoria` |
| API load history | `GET /api/v1/stats/loads` |

---

## 13. Organización Oficial del Repositorio

```
voxmetriks/                          # Raíz del monorepo
├── .cursor/                         # Reglas y skills Cursor + Spec Kit
│   ├── rules/                       # git-commits.mdc, specify-rules.mdc
│   └── skills/speckit-*/            # Comandos SDD
├── .specify/                        # Infraestructura Spec Kit (NO mover)
│   ├── memory/constitution.md       # ESTE DOCUMENTO
│   ├── templates/                   # Plantillas spec/plan/tasks
│   ├── scripts/powershell/          # Scaffolding features
│   └── workflows/                   # SDD workflows
├── .kiro/specs/                     # Specs históricas Kiro (referencia)
├── backend/
│   └── app/
│       ├── main.py                  # Entry point API
│       ├── core/                    # config, database, logger
│       ├── shared/schemas/          # Pydantic DTOs
│       └── packages/                # Dominios: streaming, analytics, users
│           ├── streaming/routes|services/
│           ├── analytics/routes|services/
│           └── users/routes|services/
├── frontend/
│   └── src/app/
│       ├── app.routes.ts            # Routing canónico
│       ├── core/                    # auth, guards, interceptors, i18n
│       ├── shared/                  # components, models, pipes
│       ├── layouts/                 # auth-layout, dashboard-layout
│       └── packages/                # Dominios mirror backend
├── elt/
│   ├── pipelines/elt_pipeline.py  # ORQUESTADOR ELT CANÓNICO
│   ├── transform/enterprise_analytics.py
│   └── extract/                     # bootstrap, download (legacy)
├── data/                            # Gitignored parcialmente
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── warehouse/voxmetrik.duckdb
├── pocketbase/                      # Migraciones PB
├── scripts/                         # dev_start.bat, validate_warehouse.py
├── specs/                           # Features Specify (creado por /speckit-specify)
├── docs/                            # Legacy — regenerar bajo spec
├── infrastructure/docker/docker-compose.yml
├── Dockerfile
├── backend/                         # FastAPI + tests (requirements.txt)
├── archive/                         # Artefactos históricos (analytics-api, DDL legacy)
├── .env.example
└── README.md
```

**Reglas estructurales:**
- MUST NOT crear dominios fuera de `packages/` sin spec.
- MUST NOT mover `.specify/` ni `.cursor/skills/speckit-*` sin `specify integration` commands.
- Nuevas features Specify van en `specs/`, NO en `.kiro/specs/`.

---

## 14. Convenciones de Nomenclatura

### 14.1 Proyecto y producto

| Contexto | Nombre oficial |
|----------|----------------|
| Producto / marca | **Voxmetriks** |
| Código interno / API metadata | **VOXMETRIK_V2** |
| Repositorio | `voxmetriks` |
| Base de datos | `voxmetrik.duckdb` |

### 14.2 Código backend (Python)

| Elemento | Convención | Ejemplo |
|--------|------------|---------|
| Packages | snake_case | `streaming`, `analytics` |
| Modules | snake_case | `track_service.py` |
| Routes prefix | `/api/v1/{resource}` | `/api/v1/tracks` |
| Functions | snake_case | `list_tracks()` |
| Pydantic models | PascalCase | `Track`, `PaginatedResponse` |
| Tables warehouse | snake_case prefix | `dim_track`, `fact_streaming`, `agg_*`, `app_*`, `ctl_*` |

### 14.3 Código frontend (TypeScript/Angular)

| Elemento | Convención | Ejemplo |
|--------|------------|---------|
| Components | kebab-case files, PascalCase class | `track-detail.component.ts` |
| Services | kebab-case + `.service.ts` | `tracks.service.ts` |
| Routes | kebab-case paths | `/audio-features` |
| Models/Interfaces | PascalCase | `Track`, `AuthResponse` |
| Signals | camelCase | `authState` |

### 14.4 Spec Kit / Git

| Elemento | Convención | Ejemplo |
|--------|------------|---------|
| Feature branch | `NNN-short-name` | `001-docker-stabilization` |
| Spec directory | `specs/NNN-short-name/` | `automation/specs/001-docker-stabilization/` |
| Short name | 2-4 words kebab-case | `user-auth`, `elt-fix` |

### 14.5 Tablas DuckDB (prefijos obligatorios)

| Prefijo | Capa |
|---------|------|
| `raw_` | Staging |
| `dim_` | Dimensión |
| `fact_` | Hecho |
| `agg_` | Agregado |
| `app_` | Aplicación (API-managed) |
| `ctl_` | Control / auditoría |

---

## 15. Reglas para Especificaciones Futuras

### 15.1 Cuándo crear spec

MUST crear spec via `/speckit-specify` cuando:

- Nueva feature visible para usuario o API pública
- Cambio breaking en contrato API
- Modificación DDL warehouse
- Cambio en pipeline ELT
- Remediación de deuda técnica TD-001 a TD-010
- Introducción de dependencia major nueva

MAY omitir spec para: typo fixes, formatting, dependency patch sin behavior change.

### 15.2 Contenido mínimo de spec.md

1. Strategic Alignment (OE/OT/OO)
2. User Stories priorizadas P1/P2/P3 — independientemente testables
3. Acceptance Scenarios (Given/When/Then)
4. Out of Scope explícito
5. Data impact assessment (warehouse/app tables afectadas)
6. Security impact assessment
7. Synthetic vs real data declaration

### 15.3 Flujo obligatorio

```
/speckit-constitution (referencia) → /speckit-specify → /speckit-clarify (si ambigüedad)
→ /speckit-checklist → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement
```

### 15.4 Coexistencia con Kiro

- `.kiro/specs/` es **read-only reference** post-ratificación.
- Nuevas specs MUST NOT crearse en `.kiro/`.
- Backlog Kiro tasks.md MAY mapearse a specs Specify individuales.

---

## 16. Reglas para Implementación

### 16.1 Principios de implementación

1. **Minimal diff:** cambios MUST ser el conjunto mínimo que satisface la spec.
2. **Match conventions:** código nuevo MUST parecer escrito por el mismo autor del dominio.
3. **No over-engineering:** no abstraer prematuramente; no helpers de una línea.
4. **Reuse services:** extender services existentes antes de duplicar SQL.

### 16.2 Orden de implementación por capa

```
1. DDL / Pipeline (si data impact)
2. Backend services + routes + Pydantic models
3. Frontend models (api.models.ts) + services + components
4. Tests
5. Docs / OpenAPI verification
```

### 16.3 Reglas backend

- SQL MUST ser parametrizado (`?` placeholders).
- Escrituras MUST usar `get_write_conn()` con lock.
- Nuevos endpoints MUST registrarse en router del dominio correspondiente.
- MUST NOT importar ORM.

### 16.4 Reglas frontend

- MUST usar standalone components.
- MUST lazy-load nuevas rutas en `app.routes.ts`.
- MUST NOT hardcodear URLs API; usar `environment.apiUrl`.
- MUST usar `TranslatePipe` para strings UI visibles.
- Dead code (componentes no importados) MUST eliminarse en spec de cleanup.

### 16.5 `/speckit-implement` prerequisites

- `tasks.md` existe y está completo.
- `/speckit-analyze` PASS (o excepción documentada).
- Checklists en `checklists/` completos (o override aprobado).

---

## 17. Reglas para UML

### 17.1 Cuándo producir UML

MUST incluir diagramas UML en `plan.md` o `design.md` de la spec cuando:

- Nueva interacción entre 3+ componentes
- Cambio en modelo de datos con 3+ entidades nuevas
- Nuevo flujo auth/autorización
- Modificación pipeline ELT con stages nuevos

### 17.2 Tipos de diagramas permitidos

| Tipo | Uso Voxmetriks | Herramienta |
|------|----------------|-------------|
| **Component Diagram** | Dominios backend/frontend | Mermaid en Markdown |
| **Sequence Diagram** | Flujos API, ELT, auth | Mermaid |
| **Entity-Relationship** | Cambios warehouse | Mermaid erDiagram |
| **Deployment Diagram** | Docker topology | Mermaid / ASCII |
| **Use Case** | Actores vs sistema | Referencia README diagram |

### 17.3 Reglas de modelado

- MUST usar nombres oficiales del Glosario.
- MUST marcar componentes `<<synthetic>>` cuando generen datos sintéticos.
- MUST alinear packages UML con `packages/` del repo.
- MUST NOT inventar componentes no existentes sin spec que los introduzca.
- Diagramas MUST vivir en repo (Markdown/Mermaid), no solo en herramientas externas.

### 17.4 Ejemplo canónico (deployment)

```mermaid
flowchart TB
    subgraph Client
        SPA[Angular SPA]
    end
    subgraph Server
        API[FastAPI app.main]
        ELT[elt_pipeline.py]
        PB[PocketBase]
    end
    subgraph Data
        DUCK[(voxmetrik.duckdb)]
    end
    SPA -->|REST /api/v1| API
    API --> DUCK
    ELT --> DUCK
    PB -->|CSV| ELT
```

---

## 18. Reglas para Seguridad

### 18.1 Postura actual (as-is — auditada)

| Control | Estado | Riesgo |
|---------|--------|--------|
| Password hash | SHA-256 sin salt | **Crítico** |
| Session tokens | UUID opaco en DuckDB | Aceptable dev; mejorar prod |
| Auth coverage | Parcial (playlists/favorites/me) | **Alto** |
| CORS | `allow_origins=["*"]` | **Alto** en prod |
| Demo credentials | `demo/demo123`, `admin/admin123` | **Alto** en prod |
| Rate limiting | Ausente | Medio |
| HTTPS | No enforced | Medio |
| Synthetic POST | Sin auth, hasta 2M filas | **Crítico** |

### 18.2 Target state (obligatorio antes de producción)

1. **Password hashing:** bcrypt o argon2 con salt — spec `security-auth-hardening`.
2. **Auth on mutations:** todo POST/PUT/DELETE de catálogo y synthetic MUST requerir Bearer token.
3. **RBAC mínimo:** roles `user`, `engineer`, `admin` — engineer para ELT/explorer (evolución de `hasEngineerAccess()`).
4. **CORS:** origins explícitos por environment.
5. **Demo seeds:** ONLY en `ENV=development`; MUST NOT existir en prod.
6. **Secrets:** `.env` gitignored; `.env.example` sin credenciales reales.
7. **Session expiry:** mantener 1d/90d; añadir endpoint logout que invalide token.
8. **SQL injection:** mantener queries parametrizadas; whitelist estricta en explorer table names (ya parcialmente implementado).

### 18.3 Reglas para implementadores

- MUST NOT loguear passwords, tokens completos ni PII en logs.
- MUST NOT commitear `.env`.
- MUST evaluar auth impact en toda spec con mutación de datos.
- MUST usar `auth_deps.resolve_session()` para endpoints protegidos.

---

## 19. Reglas para APIs

### 19.1 Estándares REST

| Atributo | Estándar |
|----------|----------|
| Base path | `/api/v1` |
| Versioning | Prefijo v1; breaking changes → v2 con spec |
| Format | JSON |
| Pagination | `page`, `limit` query params → `PaginatedResponse` |
| Errors | HTTP status codes semánticos; JSON `{detail: ...}` FastAPI default |
| Auth header | `Authorization: Bearer <token>` |
| Docs | OpenAPI auto `/docs`, `/redoc` |

### 19.2 Inventario oficial de dominios API

| Dominio | Prefix | Endpoints | Auth default |
|---------|--------|-----------|--------------|
| Artists | `/artists` | 7 | None (deuda) |
| Genres | `/genres` | 6 | None (deuda) |
| Tracks | `/tracks` | 8 | None (deuda) |
| Playlists | `/playlists` | 7 | Required |
| Favorites | `/favorites` | 3 | Required |
| Stats | `/stats` | 8 | None (deuda) |
| Analytics | `/analytics` | 8 | Mixed |
| Users | `/users` | 4 | Mixed |
| System | `/`, `/health` | 2 | None |

**Total: 54 endpoints**

### 19.3 Reglas de evolución API

- MUST actualizar `app/shared/schemas/models.py` y `frontend/.../api.models.ts` en mismo PR.
- MUST NOT eliminar endpoint sin deprecation spec y periodo de gracia documentado.
- MUST documentar auth requirements en OpenAPI `dependencies` cuando se añada auth.
- Nuevos endpoints MUST ubicarse en router del dominio correcto bajo `packages/*/routes/`.

### 19.4 Frontend integration

- `apiInterceptor` MUST continuar adjuntando token para URLs `/api/v1`.
- `environment.apiUrl` MUST apuntar a API real por environment.

---

## 20. Reglas para Data Warehouse

### 20.1 Autoridad DDL

| Fuente | Autoridad |
|--------|-----------|
| `elt/pipelines/elt_pipeline.py` DDL_STATEMENTS | **Canónica** dims/facts base |
| `elt/transform/enterprise_analytics.py` | **Canónica** enterprise layer |
| `user_storage.py`, `app_storage.py` | **Canónica** `app_*` |
| `archive/legacy/schema.sql` | **No canónica** — archivada |

### 20.2 Modelo dimensional oficial

**Dimensiones:** `dim_artista`, `dim_genero`, `dim_album`, `dim_track`, `dim_usuario`, `dim_playlist`, `dim_tiempo`

**Hechos core:** `fact_streaming`

**Hechos enterprise:** `fact_user_activity`, `fact_playlist_activity`, `fact_favorites`, `fact_searches`, `fact_stream_sessions`

**Agregados:** `agg_top_artistas`, `agg_genero_popularidad`, `agg_distribucion_energia`, `agg_tracks_populares`, `agg_daily_streams`, `agg_user_activity`, `agg_genre_trends`, `agg_artist_growth`, `agg_platform_usage`, `agg_top_playlists`, `agg_recommendation_scores`, `agg_user_engagement`, `agg_streaming_devices`, `agg_recent_activity`, `agg_top_searches`, `agg_user_retention`

### 20.3 Reglas de evolución de esquema

1. Cambios MUST ser idempotentes.
2. MUST NOT eliminar columnas sin spec de migración.
3. Audio features MUST permanecer inline en `dim_track` (no recrear `fact_audio_features` separada).
4. Nuevos agregados MUST seguir prefijo `agg_` y poblarse en pipeline o job documentado.
5. MUST ejecutar `validate_warehouse.py` post-cambio.

### 20.4 Queries backend

- MUST usar schema introspection antes de SELECT con columnas opcionales.
- MUST NOT `SELECT *` en endpoints públicos sin límite.
- Explorer preview MUST validar table name contra whitelist.

---

## 21. Reglas para ETL

### 21.1 Entry point canónico

```bash
python analytics/elt/pipelines/elt_pipeline.py
```

**NO usar:** `python elt_pipeline.py` (raíz — no existe).

### 21.2 Fuentes de ingesta (orden de precedencia)

1. PocketBase `datasets` collection (CSV)
2. `data/bronze/raw_spotify.parquet`
3. `elt/extract/bootstrap_catalog.py` (synthetic catalog fallback)

### 21.3 Stages obligatorios

| Stage | Función | Registro |
|-------|---------|----------|
| Extract Bronze | Landing raw | `ctl_carga_dataset` |
| Transform Silver | Clean/conform | pipeline stages |
| Load Gold | DuckDB + parquet export | `ctl_carga_dataset`, `ctl_auditoria` |
| Enterprise | Synthetic behavioral | `ctl_pipeline_stages` |
| Verify | Counts validation | logs + `validate_warehouse.py` |

### 21.4 Reglas operativas

- Pipeline MUST ser idempotente y re-ejecutable.
- MUST NOT modificar `app_*` tables desde ELT.
- Failures MUST exit code != 0 (Docker `depends_on` lo requiere).
- Config MUST leer `.env` compartido con API.
- Legacy scripts (`download_dataset.py`, `csv_to_parquet.py`) MUST NOT usarse en flujos nuevos sin spec de revivals.

### 21.5 Docker

- Compose service `pipeline` MUST ejecutar entry point canónico.
- Dockerfile MUST copiar `elt/` completo (remediación TD-002).

---

## 22. Criterios de Aceptación Globales del Proyecto

Todo release (minor o major) MUST satisfacer:

### 22.1 Funcionales

- [ ] Pipeline ELT completa exitosamente desde fuente configurada
- [ ] `GET /health` retorna status OK con warehouse poblado
- [ ] Frontend autentica y navega rutas protegidas
- [ ] CRUD catálogo operativo (artists, genres, tracks)
- [ ] Playlists y favorites operativos con auth
- [ ] Dashboard analytics renderiza KPIs desde API
- [ ] Explorer lista y preview tablas warehouse

### 22.2 No funcionales

- [ ] API responde en < 2s p95 para queries paginadas estándar (dev hardware)
- [ ] Pipeline completa en tiempo documentado para dataset default
- [ ] Zero secrets en repositorio Git
- [ ] Constitución versionada y vigente

### 22.3 Calidad

- [ ] Tests backend verdes (cuando TD-001 remediado)
- [ ] Tests frontend verdes (cuando corregido app.spec.ts)
- [ ] `/speckit-analyze` PASS para features del release
- [ ] OpenAPI alineada con implementación

### 22.4 Documentación

- [ ] Runbook operativo único y validado (`dev_start.bat` + doc generada)
- [ ] Specs de features del release en `specs/`
- [ ] Deuda técnica TD-* del release cerrada o diferida con spec

---

## 23. Restricciones del Proyecto

### 23.1 Restricciones tecnológicas inmutables

| Restricción | Justificación |
|-------------|---------------|
| Python 3.12 only | Wheels duckdb/pyarrow/pydantic |
| No ORM | Patrón establecido routes→services→SQL |
| DuckDB file-based | Arquitectura warehouse actual |
| Angular standalone (no NgModules) | 42 componentes ya standalone |
| No microservicios | Modular monolith suficiente para escala actual |
| Medallion ELT | Pipeline implementado y funcional |

### 23.2 Restricciones de proceso

| Restricción | Descripción |
|-------------|-------------|
| No reescritura | §5 P1 |
| Spec before implement (non-trivial) | §15 |
| Constitution prevalece | Governance |
| Kiro superseded by Specify | §11.4 |
| No commit datos binarios | `.gitignore` |

### 23.3 Restricciones de producto

| Restricción | Descripción |
|-------------|-------------|
| No streaming audio real | Player demo WAV |
| Datos enterprise synthetic | No presentar como telemetría real |
| PocketBase solo ingesta | No auth provider API |

### 23.4 Restricciones de seguridad (hasta remediación)

- Demo credentials permitidas **solo** en development
- CORS `*` permitido **solo** en development
- CRUD sin auth es **deuda temporal**, no patrón target

---

## 24. Glosario Empresarial de Voxmetriks

| Término | Definición |
|---------|------------|
| **Voxmetriks** | Plataforma empresarial de streaming musical y analítica de datos |
| **VOXMETRIK_V2** | Identificador interno del codebase y metadata API |
| **Medallion Architecture** | Patrón de capas Bronze (raw) → Silver (clean) → Gold (curated) |
| **Bronze** | Capa raw landing en Parquet (`data/bronze/`) |
| **Silver** | Capa cleaned/conformed (`data/silver/`) |
| **Gold** | Capa analytics-ready: DuckDB + export Parquet (`data/gold/`) |
| **Warehouse** | DuckDB OLAP con modelo dimensional en `voxmetrik.duckdb` |
| **Enterprise Layer** | Extensión synthetic behavioral generada por `enterprise_analytics.py` |
| **Synthetic Data** | Datos generados algorítmicamente, no telemetría real |
| **Catalog Data** | Datos de tracks/artists/genres del dataset fuente |
| **Package** | Dominio de código (`streaming`, `analytics`, `users`) |
| **app_* tables** | Tablas de aplicación gestionadas por API (usuarios, playlists) |
| **ctl_* tables** | Tablas de control y auditoría del pipeline |
| **dim_* / fact_* / agg_*** | Prefijos del modelo dimensional warehouse |
| **ELT** | Extract-Load-Transform; carga antes de transformación en DuckDB |
| **Pipeline** | Orquestador batch `elt/pipelines/elt_pipeline.py` |
| **PocketBase** | Servicio opcional de ingesta CSV (colección `datasets`) |
| **Specify / Spec Kit** | Toolkit GitHub SDD con CLI `specify` y skills `/speckit-*` |
| **Constitution** | Este documento; principios supremos del proyecto |
| **Spec** | Especificación formal en `specs/NNN-*/spec.md` |
| **OE/OT/OO** | Objetivo Estratégico / Táctico / Operativo |
| **CU / HU** | Caso de Uso / Historia de Usuario |
| **SDD** | Spec-Driven Development |
| **Modular Monolith** | Monolito con separación lógica por packages |
| **Schema Introspection** | Patrón DESCRIBE/safe_query antes de asumir columnas |
| **Engineer Access** | Rol con acceso a ELT pipeline UI y warehouse explorer |
| **Demo Player** | Reproductor HTML5 Audio con WAV locales, no streaming backend |
| **OpenAPI** | Contrato API auto-generado en `/docs` |
| **Deuda Técnica (TD-NNN)** | Registro de gaps conocidos §9.4 |
| **Definition of Done** | Criterios §9.3 para cerrar features |
| **Constitution Check** | Gate en plan.md validando compliance con esta Constitución |

---

## Governance

### Supremacía

Esta Constitución **prevalece** sobre:
- Documentación en `docs/`, `quickstart.md` (raíz → `docs/quickstart.md`)
- Specs Kiro no migradas a Specify
- Decisiones ad hoc no registradas en specs
- Sugerencias de agentes IA que contradigan principios ratificados

El **código fuente** prevalece sobre documentación legacy para describir comportamiento actual, pero **esta Constitución** prevalece sobre el código para definir comportamiento **target** y restricciones de evolución.

### Procedimiento de enmienda

1. Crear spec `specs/NNN-constitution-amendment/` describiendo cambio propuesto.
2. Documentar impacto en principios, templates y deuda técnica.
3. Ejecutar `/speckit-plan` y `/speckit-analyze`.
4. Actualizar `.specify/memory/constitution.md` con versión semver:
   - **MAJOR:** eliminación/redefinición de principio incompatible
   - **MINOR:** nuevo principio o sección material
   - **PATCH:** clarificaciones, typos, refinamientos
5. Actualizar `Last Amended` con fecha ISO.
6. Propagar cambios a templates Specify si aplica.

### Compliance review

- Todo PR MUST verificar Constitution Check cuando tenga spec asociada.
- Todo agente IA (Cursor `/speckit-*`) MUST leer esta Constitución antes de specify/plan/implement.
- Violaciones MUST documentarse como deuda técnica TD-NNN o remediarse en el mismo PR.

### Agentes IA

Los skills en `.cursor/skills/speckit-*` operan bajo esta Constitución. El contexto dinámico en `.cursor/rules/specify-rules.mdc` MUST apuntar al plan activo sin contradecir principios aquí definidos.

---

**Version**: 1.0.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-06-19

*Documento generado conforme a GitHub Spec Kit v0.11.3 y auditoría arquitectónica Voxmetriks 2026-06-19.*
