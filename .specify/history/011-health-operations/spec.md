> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Salud y Operaciones de Plataforma

**Feature Branch**: `011-health-operations`  
**Feature Directory**: `specs/011-health-operations/`  
**Created**: 2026-06-20  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de salud básica de plataforma: health check API, metadata raíz, indicadores en Settings tab API, verificación Docker Compose, scripts CLI de validación warehouse, y arranque con validación DuckDB — **sin** observabilidad enterprise.

**Prerrequisitos:** `001-user-identity-access` (sesión para `/settings`); API FastAPI desplegada; spec **006** para superficie settings compartida.

**Evidencia base:** `SPEC-008-011-EVIDENCE-AUDIT.md` v1.0.0 (2026-06-20); `backend/app/main.py`, `settings.component.*`, `docker-compose.yml`, `scripts/validate_warehouse.py`, `scripts/analyze_warehouse.py`. Esta spec **no** introduce capacidades ausentes en código.

---

## Delimitación obligatoria: Spec 006 vs Spec 011

La ruta `/settings` comparte **tabs** pero **responsabilidades documentales distintas**:

| Aspecto | Spec **006** — Autogestión de cuenta | Spec **011** — Salud y operaciones |
|---------|--------------------------------------|-------------------------------------|
| **Propósito** | Preferencias personales, perfil, privacidad, tema, idioma | Salud API, disponibilidad, verificación operativa mínima |
| **OO/OT** | OO-10/OO-11, OT-06 | OO-17, OT-10 |
| **Tabs UI** | `general` (prefs usuario) | `api` (health + referencias endpoints) |
| **Tabs compartidos** | Visibilidad engineer tabs → **008** contenido | — |
| **CU propietarios** | CU-ST01–ST04 prefs; CU-ST05 health *consumo* | CU-HO* health *contrato* y operaciones |
| **Endpoints** | Consume `/health` vía FR-ST09 | Define contrato `/health`, `/` |
| **Operaciones** | ❌ | Docker healthcheck, CLI scripts, lifespan startup |

**Regla de no duplicidad:** Spec **006** documenta que el usuario **puede ver** health en settings (CU-ST05, FR-ST09–ST10). Spec **011** documenta **qué** responde `/health`, **cómo** se verifica operativamente, y **límites** del monitoreo actual — sin redefinir preferencias de cuenta.

**Estado actual (evidencia):** No existe ruta `/operations`, Prometheus, Grafana, auto-refresh periódico health, ni UI para `GET /`.

---

## Contexto Empresarial

Voxmetriks requiere transparencia operativa mínima (Constitución §4.3 nivel operativo): operadores y usuarios autenticados MUST poder **verificar** que la API responde y el warehouse DuckDB es accesible, sin suite APM enterprise.

La auditoría (`SPEC-008-011-EVIDENCE-AUDIT.md`) confirmó implementación ~62 % ponderada (health ~85 %; “operations” ampliadas ~25 %):

- `GET /health` con `HealthResponse` (status, database, tables, version).
- `GET /` metadata raíz (app, version, docs, health).
- Settings tab `api`: banner estado, refresh manual, referencias URL estáticas.
- Docker Compose: `depends_on` pipeline→api; `healthcheck` contra `/health`.
- Scripts CLI: `scripts/validate_warehouse.py`, `scripts/analyze_warehouse.py` (sin UI).
- **Ausente:** `/api/info`, monitoreo centralizado, métricas infra, alerting, UI root metadata.

Spec **006** incluye health en CU-ST05. Esta spec cierra la brecha SDD de **salud y operaciones básicas** — acotada a evidencia real.

---

## Problema

### Situación actual

Operadores y usuarios autenticados necesitan:

1. **Consultar** estado API/warehouse vía `/health`.
2. **Visualizar** indicador en Settings tab API.
3. **Refrescar** health manualmente bajo demanda.
4. **Integrar** metadata raíz vía `GET /` (externo, sin UI).
5. **Orquestar** arranque Docker con healthcheck container.
6. **Validar** warehouse post-ELT vía scripts CLI.

Riesgos sin especificación formal:

- Overlap 006/011 sin frontera CU/FR.
- Inventar observabilidad enterprise (Prometheus, ELK) inexistente.
- Documentar `/api/info` (test legacy; endpoint ausente).
- Asumir info card settings es live data de `GET /` (es estática/hardcoded).

### Problema de negocio

**Voxmetriks no puede auditar operaciones básicas** si health — único mecanismo de transparencia en SPA — carece de contrato API formal, delimitación con autogestión (**006**), y límites explícitos frente a “operations suite” no implementada.

---

## Objetivo

Gobernar la **capacidad operativa de Salud y Operaciones de Plataforma (alcance mínimo verificado)**:

1. Documentar contratos `GET /health` y `GET /`.
2. Documentar UI health en Settings tab `api` (refresh manual, estados).
3. Documentar verificación Docker Compose (depends_on, healthcheck).
4. Documentar scripts CLI operativos warehouse (sin SPA).
5. Delimitar frente a **006** preferencias vs **011** salud/ops.
6. Excluir explícitamente observabilidad no implementada.
7. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU→FR→CA.

**Resultado esperado:** trazabilidad auditable de health básico y operaciones mínimas verificables en repo, sin dashboards o métricas inventadas.

---

## Alcance (Scope)

### In Scope (evidencia implementada)

- `GET /health`, `GET /`.
- Modelo `HealthResponse`.
- Lifespan startup validación DB (logging).
- Settings tab `api`: health banner, refresh, loading/error.
- `StatsService.getHealth()`.
- Docker Compose `depends_on` pipeline; API `healthcheck` `/health`.
- CLI `scripts/validate_warehouse.py`, `scripts/analyze_warehouse.py`.

### In Scope parcial

- Info card tab API: URLs/docs **estáticas** (no fetch `GET /`).
- Tests `test_api.py` legacy desalineados con schema actual (documentado, no requisito).

### Out of Scope

Ver sección **Out of Scope** al final.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma confiable con analítica de datos gobernada |
| **OT-10** | Objetivo Táctico | Habilitar observabilidad y transparencia API básica |
| **OO-17** | Objetivo Operativo | Operar verificación de salud API/warehouse y operaciones mínimas de plataforma |
| **M-17A** | Meta | GET `/health` responde ≤ 2 s p95 con DB local presente |
| **M-17B** | Meta | 100 % DB ausente retorna `status=degraded` (no HTTP 500) |
| **M-17C** | Meta | 100 % fetch health fallido en UI muestra error sin crash SPA |
| **M-17D** | Meta | 0 auto-refresh periódico health en SPA (solo manual — estado actual) |
| **DEP-01** | Departamento | **Plataforma de Producto** |
| **PKG-05** | Paquete | `administration/settings` (UI health); backend `app/main.py` (endpoints root) |

---

## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../README.md) — filas 011 pendientes integración post-ratificación.

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-HO01 | US-HO01 | FR-HO06 | CA-001 |
| CU-HO01 | US-HO01 | FR-HO08 | CA-001 |
| CU-HO01 | US-HO01 | FR-HO09 | CA-001 |
| CU-HO01 | US-HO01 | FR-HO11 | CA-002 |
| CU-HO02 | US-HO02 | FR-HO10 | CA-003 |
| CU-HO02 | US-HO02 | FR-HO06 | CA-003 |
| CU-HO04 | US-HO01 | FR-HO01 | CA-004 |
| CU-HO04 | US-HO01 | FR-HO02 | CA-004 |
| CU-HO04 | US-HO01 | FR-HO03 | CA-004 |
| CU-HO04 | US-HO04 | FR-HO07 | CA-005 |
| CU-HO04 | US-HO04 | FR-HO08 | CA-005 |
| CU-HO04 | US-HO04 | FR-HO12 | CA-006 |
| CU-HO03 | US-HO03 | FR-HO04 | CA-007 |
| CU-HO05 | US-HO05 | FR-HO14 | CA-008 |
| CU-HO05 | US-HO05 | FR-HO15 | CA-008 |
| CU-HO05 | US-HO05 | FR-HO18 | CA-008 |
| CU-HO06 | US-HO05 | FR-HO16 | CA-009 |
| CU-HO06 | US-HO05 | FR-HO17 | CA-009 |
| CU-HO01 | US-HO01 | FR-HO19 | CA-010 |

### Matriz de trazabilidad operativa (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17B | DEP-01 | PKG-05 | CU-HO04 | US-HO01 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17C | DEP-01 | PKG-05 | CU-HO04 | US-HO04 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17D | DEP-01 | PKG-05 | CU-HO02 | US-HO02 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO03 | US-HO03 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO05 | US-HO05 | 011 | Implementado |
| OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO06 | US-HO05 | 011 | Implementado |

---

## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Autenticado** | Accede `/settings` tab API | Ver salud básica servicio |
| **Operador / DevOps** | Ejecuta Docker Compose y scripts CLI | Verificar despliegue y warehouse |
| **Integrador externo** | Consume `GET /` y `/health` sin SPA | Metadata y health programático |
| **Sistema Voxmetriks API** | Lifespan + health endpoint | Reportar ok/degraded/error |

---

## Casos de Uso

### CU-HO01: Consultar health en Settings tab API

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO01 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Sesión válida; en `/settings` |
| **Flujo principal** | 1. Usuario abre settings → 2. `ngOnInit` llama `refreshHealth()` → 3. `StatsService.getHealth()` → GET `/health` → 4. UI muestra banner status + meta versión DuckDB |
| **Postcondición** | Estado visible o error degradado |
| **Flujo alternativo** | 3a. Usuario selecciona tab `api` → `refreshHealth()` again |
| **Delimitación** | Tab `general` prefs → **006** |
| **Reglas de negocio** | RB-HO06, RB-HO08 |

### CU-HO02: Refrescar health manualmente

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO02 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Tab `api` visible |
| **Flujo principal** | 1. Usuario pulsa “Actualizar health check” → 2. `healthLoading=true` → 3. Fetch `/health` → 4. Actualiza banner |
| **Postcondición** | Datos health actualizados o error |
| **Nota** | **No** existe polling automático (RB-HO07) |
| **Reglas de negocio** | RB-HO07 |

### CU-HO03: Consultar metadata API raíz

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO03 |
| **Actor principal** | Integrador externo |
| **Precondición** | API accesible |
| **Flujo principal** | 1. GET `/` → 2. Respuesta JSON `{app, version, docs, health}` |
| **Postcondición** | Metadata disponible |
| **Nota** | **Sin UI SPA** para este endpoint |
| **Reglas de negocio** | RB-HO01 |

### CU-HO04: Evaluar estados health API

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO04 |
| **Actor principal** | Sistema Voxmetriks API / UI |
| **Precondición** | Request GET `/health` |
| **Flujo principal** | 1. Si DB file missing → `status=degraded`, tables=[] → 2. Si DB OK → connect, list tables, DuckDB version → `status=ok` → 3. Si exception → `status=error` |
| **Postcondición** | HealthResponse coherente |
| **Reglas de negocio** | RB-HO02, RB-HO03 |

### CU-HO05: Verificar servicios vía Docker Compose

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO05 |
| **Actor principal** | Operador / DevOps |
| **Precondición** | Docker Compose disponible |
| **Flujo principal** | 1. Servicio `pipeline` completa exitosamente → 2. Servicio `api` arranca tras `depends_on: service_completed_successfully` → 3. Container healthcheck consulta `http://localhost:8000/health` periódicamente |
| **Postcondición** | API operativa tras pipeline OK |
| **Reglas de negocio** | RB-HO04, RB-HO05 |

### CU-HO06: Validar warehouse vía scripts CLI

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HO06 |
| **Actor principal** | Operador / DevOps |
| **Precondición** | Warehouse poblado post-ELT |
| **Flujo principal** | 1. Ejecutar `python scripts/validate_warehouse.py` y/o `scripts/analyze_warehouse.py` → 2. Scripts imprimen conteos tablas fact/agg, tamaño DB, parquet count |
| **Postcondición** | Validación manual stdout |
| **Nota** | **Sin integración SPA** |
| **Reglas de negocio** | RB-HO09 |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-HO01 — Ver salud API en settings (Priority: P1)

Como **Usuario Autenticado**, quiero **ver el estado del backend en Settings tab API**, para **saber si el servicio está operativo**.

**Why this priority**: Única superficie health en SPA; OO-17; complementa CU-ST05 **006** a nivel contrato.

**Independent Test**: Abrir `/settings` tab API; banner muestra ok/degraded/error o error conexión; meta versión visible si OK.

**Acceptance Scenarios**:

1. **Given** API healthy, **When** tab api carga, **Then** banner status-ok y texto tablas count (FR-HO01, FR-HO08, FR-HO09).
2. **Given** health OK, **When** renderiza meta, **Then** muestra `v{version} · DuckDB` (FR-HO11).
3. **Given** info card, **When** visible, **Then** muestra apiUrl estático y referencias docs/health URLs (FR-HO13).

**Maps to**: CU-HO01, CU-HO04 | FR-HO01, FR-HO06, FR-HO08–FR-HO09, FR-HO11, FR-HO13 | M-17A

*Delimitación:* tema/idioma/privacidad → **006** tab `general`.

---

### User Story US-HO02 — Refrescar health manualmente (Priority: P1)

Como **Usuario Autenticado**, quiero **actualizar el health check bajo demanda**, para **ver estado reciente sin recargar la página**.

**Acceptance Scenarios**:

1. **Given** tab api, **When** pulsa refresh, **Then** `healthLoading` true y botón disabled (FR-HO10).
2. **Given** refresh completa, **When** OK, **Then** health signal actualizado (FR-HO06).

**Maps to**: CU-HO02 | FR-HO06, FR-HO10 | M-17D

---

### User Story US-HO03 — Metadata API raíz (Priority: P2)

Como **Integrador externo**, quiero **consultar GET /**, para **obtener app name, versión y rutas docs/health**.

**Acceptance Scenarios**:

1. **Given** API running, **When** GET `/`, **Then** JSON con app, version, docs, health paths (FR-HO04).
2. **Given** integrador, **When** busca UI root metadata, **Then** **no** existe pantalla SPA (Out of Scope UI root).

**Maps to**: CU-HO03 | FR-HO04

---

### User Story US-HO04 — Estados loading y error (Priority: P1)

Como **Sistema Voxmetriks**, debo **degradar health UI sin exponer internals**, para **cumplir M-17C y alinear RB-ST06**.

**Acceptance Scenarios**:

1. **Given** fetch health falla, **When** error handler, **Then** `healthError=true`, mensaje contacto `/health`, sin stack trace (FR-HO12, RB-HO08).
2. **Given** loading, **When** fetch en curso, **Then** status-warn y texto “Comprobando…” (FR-HO07).
3. **Given** status degraded, **When** DB missing, **Then** mensaje degradado warehouse (FR-HO08, M-17B).

**Maps to**: CU-HO04, CU-HO01 | FR-HO07, FR-HO08, FR-HO12 | M-17B, M-17C

---

### User Story US-HO05 — Operaciones Docker y CLI (Priority: P2)

Como **Operador**, quiero **orquestar servicios y validar warehouse fuera de SPA**, para **operaciones básicas de plataforma**.

**Acceptance Scenarios**:

1. **Given** docker-compose, **When** pipeline exit 0, **Then** api arranca (FR-HO15).
2. **Given** container api, **When** healthcheck runs, **Then** consulta GET `/health` (FR-HO14).
3. **Given** post-ELT, **When** ejecuta validate_warehouse.py, **Then** imprime conteos fact/agg (FR-HO16).

**Maps to**: CU-HO05, CU-HO06 | FR-HO14–FR-HO17 | Operaciones CLI

---

### Edge Cases

- **DB path exists but corrupt**: health returns `status=error`, tables=[].
- **Health version field**: en OK es DuckDB `SELECT version()`; en degraded/error es `"2.0.0"` app version string.
- **getHealth URL**: strip `/api/v1` from environment.apiUrl before `/health`.
- **Settings init**: refreshHealth on ngOnInit even if tab not api (evidencia L130).
- **test_api.py legacy**: espera `/api/info` y root `{status:running}` — **no** requisitos 011.
- **No periodic refresh**: autoRefresh pref pipeline (**008**) no aplica health.

---

## Requirements *(mandatory)*

### Functional Requirements — API Health

- **FR-HO01**: System MUST expose `GET /health` returning `HealthResponse`: `status`, `database`, `tables`, `version`.
- **FR-HO02**: When database file does not exist, `/health` MUST return `status="degraded"`, empty `tables`, without raising HTTP 500.
- **FR-HO03**: When database connects successfully, `/health` MUST return `status="ok"`, `tables` from `list_tables(conn)`, `version` from DuckDB `SELECT version()`.
- **FR-HO04**: System MUST expose `GET /` returning JSON: `app`, `version`, `docs`, `health` path references.
- **FR-HO05**: On unhandled DB exception in health, MUST return `status="error"` with empty tables and logged error.

### Functional Requirements — API Lifespan

- **FR-HO18**: Application lifespan startup MUST log database path; if missing log error hinting ELT; if present validate tables and ensure user/app tables.

### Functional Requirements — Frontend Health UI

- **FR-HO06**: Settings MUST call `refreshHealth()` on component init and when user selects tab `api`.
- **FR-HO07**: UI MUST map health states to CSS classes: loading/error connection → `status-warn`; `ok` → `status-ok`; `degraded` → `status-warn`; other → `status-error`.
- **FR-HO08**: UI MUST display localized status text for loading, connection error, ok (with table count), degraded (DB not found), and unknown status.
- **FR-HO09**: UI MUST display health meta `v{version} · DuckDB` when fetch succeeds without error.
- **FR-HO10**: Refresh button MUST disable while `healthLoading` is true.
- **FR-HO11**: `StatsService.getHealth()` MUST request `{apiRoot}/health` where apiRoot strips `/api/v1` suffix from `environment.apiUrl`.
- **FR-HO12**: On health fetch error, UI MUST set `healthError` without displaying stack traces or raw connection strings in banner (align **006** RB-ST06).
- **FR-HO13**: Tab API info card MUST display static reference values: `environment.apiUrl`, hardcoded docs URL, hardcoded health URL — **not** live fetch from `GET /`.

### Functional Requirements — Docker Operations

- **FR-HO14**: Docker Compose service `api` MUST define healthcheck probing `http://localhost:8000/health` with interval/timeout/retries as configured.
- **FR-HO15**: Docker Compose service `api` MUST depend on `pipeline` with `condition: service_completed_successfully`.

### Functional Requirements — CLI Operations

- **FR-HO16**: Repository MUST provide `scripts/validate_warehouse.py` printing fact table row counts, agg table counts, DB size, parquet file count — executable manually post-ELT.
- **FR-HO17**: Repository MAY provide `scripts/analyze_warehouse.py` for extended warehouse analysis CLI — **no SPA integration**.

### Functional Requirements — Delimitación 006

- **FR-HO19**: Spec **011** owns health API contract and operational verification FRs; Spec **006** FR-ST09–ST10 reference consumer behavior on tab API without redefining `/health` schema.

---

## Non-Functional Requirements

- **NFR-HO01 (Performance)**: GET `/health` SHOULD respond ≤ 2 s p95 with local DuckDB file present (M-17A).
- **NFR-HO02 (Reliability)**: Missing DB MUST NOT crash health endpoint (M-17B).
- **NFR-HO03 (UX)**: Health UI MUST show distinct loading, success, and error states (M-17C).
- **NFR-HO04 (Security — UI)**: Health banner MUST NOT expose credentials; SHOULD minimize sensitive path exposure in user-facing text (align RB-ST06).
- **NFR-HO05 (Operations)**: Docker healthcheck MUST use same `/health` endpoint as SPA.
- **NFR-HO06 (Scope honesty)**: Feature MUST NOT claim centralized monitoring, APM, or infra metrics.
- **NFR-HO07 (Maintainability)**: CU→FR→CA matrix and 006/011 boundary documented in spec.
- **NFR-HO08 (Availability)**: Health endpoint MUST be reachable without authentication (evidencia: no auth on `/health`).
- **NFR-HO09 (i18n)**: Tab API labels MUST support ES/EN via settings i18n keys where defined.
- **NFR-HO10 (Traceability)**: Operational scripts documented as CLI-only, not product UI features.

---

## Reglas de Negocio

- **RB-HO01**: `GET /` and `GET /health` are public endpoints without session requirement in current implementation.
- **RB-HO02**: Health `status` MUST be one of `ok`, `degraded`, `error` as implemented in `main.py`.
- **RB-HO03**: Degraded status specifically indicates missing database file path.
- **RB-HO04**: Docker Compose MUST NOT start API until pipeline job completes successfully when using default compose file.
- **RB-HO05**: Container healthcheck MUST target same `/health` contract as SPA.
- **RB-HO06**: Spec **006** owns user preference tabs and CU-ST05 consumer story; **011** owns health contract depth.
- **RB-HO07**: Health refresh in SPA is **manual only**; no periodic auto-refresh timer exists.
- **RB-HO08**: UI error messages MUST be user-oriented (“No se pudo contactar el backend en /health”) without stack traces.
- **RB-HO09**: CLI warehouse scripts are operational utilities outside SDD UI scope; validación es stdout-only.
- **RB-HO10**: Endpoint `/api/info` MUST NOT be specified — it does not exist in `main.py`.
- **RB-HO11**: Info card API version label “v1” in settings is static UI reference to API prefix, distinct from DuckDB version in health banner.

---

## Criterios de Aceptación Globales

1. **CA-001**: Tab API muestra banner health tras fetch init/select (CU-HO01).
2. **CA-002**: Meta versión DuckDB visible cuando health OK (FR-HO09).
3. **CA-003**: Botón refresh actualiza health y respeta loading state (CU-HO02).
4. **CA-004**: GET `/health` retorna ok/degraded/error según DB state (CU-HO04).
5. **CA-005**: UI loading/error/degraded mapeados correctamente (US-HO04).
6. **CA-006**: Error fetch no crash SPA ni muestra stack (FR-HO12).
7. **CA-007**: GET `/` retorna metadata app/version/docs/health (CU-HO03).
8. **CA-008**: Docker compose depends_on y healthcheck documentados (CU-HO05).
9. **CA-009**: Scripts CLI validate/analyze warehouse ejecutables manualmente (CU-HO06).
10. **CA-010**: Preferencias usuario tab general no son requisitos 011 (delimitación 006).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-HO01**: 95% GET `/health` con DB local responden ≤ 2 s p95 (M-17A).
- **SC-HO02**: 100% requests con DB file missing retornan `status=degraded` HTTP 200 (M-17B).
- **SC-HO03**: 100% fetch health fallidos en UI muestran error banner sin uncaught exception (M-17C).
- **SC-HO04**: 0 implementaciones auto-polling health en SPA verificadas por código (M-17D).
- **SC-HO05**: 0 endpoints inventados (`/api/info`, Prometheus) en spec 011 (evidencia audit).
- **SC-HO06**: Documentación frontera 006/011 presente y auditable (RB-HO06).
- **SC-HO07**: Docker healthcheck y CLI scripts referenciados como únicas ops avanzadas verificadas en repo.

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-HO01 | Duplicidad CU-ST05 vs CU-HO01 | Alta | Medio | Tabla delimitación; FR-HO19 |
| R-HO02 | Nombre “Operations” sobredimensiona alcance | Alta | Medio | Out of Scope APM; RB-HO09 CLI only |
| R-HO03 | Inventar `/api/info` | Media | Alto | RB-HO10, Out of Scope |
| R-HO04 | Info card confundida con live root API | Media | Medio | FR-HO13, RB-HO11 |
| R-HO05 | Health expone database path en JSON API | Baja | Bajo | UI no muestra path; NFR-HO04 |
| R-HO06 | Tests legacy desalineados | Media | Bajo | Documentado; no requisito 011 |
| R-HO07 | Usuario espera monitoreo 24/7 | Media | Alto | Out of Scope; SC-HO04 |
| R-HO08 | PocketBase health no en SPA | Baja | Bajo | Out of Scope |
| R-HO09 | Warehouse/pipeline tabs confundidos con 011 | Media | Medio | Delimitación → **008** |
| R-HO10 | OT-10 overlap roadmap docs | Baja | Bajo | OO-17 específico steward platform health |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| `001-user-identity-access` | Hard | authGuard para `/settings` |
| `006-account-self-service` | Soft | Superficie settings; delimitación prefs vs health |
| `008-pipeline-monitoring` | Soft | Pipeline popula DB verificada por health |
| DuckDB warehouse file | Hard | Health ok/degraded logic |
| `StatsService.getHealth` | Hard | Cliente FE health |
| `SettingsComponent` tab `api` | Hard | UI health |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | §4.3 operativo; §18 seguridad UI |
| `SPEC-008-011-EVIDENCE-AUDIT.md` | Evidencia única alcance 011 |
| `006-account-self-service/spec.md` | CU-ST05, FR-ST09–ST10 consumer |

### Dependencias externas

| Dependencia | Descripción |
|-------------|-------------|
| Docker (opcional) | Compose healthcheck |
| Python CLI | Scripts validate/analyze warehouse |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§4.3 Nivel Operativo** | Health, compose, CLI scripts |
| **§5 P6 Warehouse** | Health verifica acceso DuckDB |
| **§12 Trazabilidad** | OT-10, OO-17, M-17A–D |
| **§14 Nomenclatura** | Branch `011-health-operations` |
| **§18 Seguridad UI** | NFR-HO04, FR-HO12 align RB-ST06 |

---

## Out of Scope

- Prometheus, Grafana, ELK, OpenTelemetry, Datadog, o APM enterprise.
- Dashboard operaciones dedicado; ruta `/operations`.
- UI para `GET /` root metadata.
- Endpoint `/api/info` (no existe).
- Auto-refresh periódico health en SPA.
- Métricas CPU/memoria/latencia p95 runtime.
- Estado PocketBase en SPA health.
- Alerting, incidentes, SLA monitoring.
- Integración SPA de scripts CLI warehouse.
- Tabs settings `warehouse`/`pipeline` (**008**).
- Preferencias usuario tab `general` (**006**).

---

## Assumptions

- API escucha en puerto 8000 en dev (referencias localhost en UI estática).
- `environment.apiUrl` termina en `/api/v1` para construcción correcta `/health`.
- Usuario autenticado accede settings; `/health` público sin auth.
- Operador ejecuta scripts CLI con Python y warehouse path default del repo.
- Docker Compose es entorno opcional de despliegue demo.
- Idiomas ES/EN para labels settings tab API.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — evidencia `SPEC-008-011-EVIDENCE-AUDIT.md`  
**Next Step**: `/speckit-checklist` → `/speckit-plan` — delimitación referencial 006 CU-ST05 recomendada post-ratificación 011.
