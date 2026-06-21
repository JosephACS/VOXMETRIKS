# Feature Specification: Explorador de Datos Warehouse

**Feature Branch**: `009-data-explorer`  
**Feature Directory**: `specs/009-data-explorer/`  
**Created**: 2026-06-20  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de inspección read-only del warehouse DuckDB: listado de tablas con metadatos, preview paginado de filas, filtro de tablas, clasificación por tipo, visualización de esquema y SQL ejecutado, panel de historial de cargas ELT, y acceso restringido a rol engineer.

**Prerrequisitos:** `001-user-identity-access` (sesión, `authGuard`, `engineerGuard`, RB-015); warehouse DuckDB accesible con tablas en schema `main`; spec **008** opcional para contexto cargas (`ctl_carga_dataset`).

**Evidencia base:** `SPEC-008-011-EVIDENCE-AUDIT.md` v1.0.0 (2026-06-20); código `explorer/*`, `analytics_service.py`, `analytics.py`. Esta spec **no** introduce capacidades ausentes en código.

**Delimitación vs otras specs (evitar duplicidad):**

| Dominio | Spec propietaria | Spec 009 |
|---------|------------------|----------|
| Auth / sesión / engineerGuard | 001 | ❌ Consume identidad y rol engineer FE |
| Monitoreo pipeline / synthetic | 008 | ❌ Solo panel loads comparte endpoint |
| Dashboards analíticos consumo BI | 007 | ❌ |
| CRUD steward catálogo | 010 | ❌ |
| Health / settings | 006 / 011 | ❌ |
| Estado warehouse capas Medallion | 008 | ❌ `GET /analytics/warehouse` no usado en explorer |

**Delimitación crítica (evidencia código):** Explorer MUST ser **read-only**. Preview ejecuta `SELECT *` paginado server-side con whitelist de nombres de tabla (`information_schema`); **no** existe editor SQL libre, export ni mutaciones desde UI.

---

## Contexto Empresarial

Voxmetriks expone un warehouse Medallion DuckDB (Constitución §3.1 In Scope — explorer; P6 warehouse read-only para inspección). Los **data engineers** MUST poder **navegar** tablas del warehouse, **inspeccionar** esquema y filas paginadas, y **consultar** historial de cargas en contexto — sin alterar datos.

La auditoría de evidencia (`SPEC-008-011-EVIDENCE-AUDIT.md`) confirmó implementación ~91 % sin spec dedicada:

- Ruta UI `/explorer` (`ExplorerComponent`) con KPIs por tipo, sidebar filtrable, preview paginado, esquema, SQL mostrado, panel loads.
- APIs: `GET /analytics/explorer/tables`, `GET /analytics/explorer/preview/{table_name}`.
- Panel cargas: `GET /stats/loads` (limit 10) — endpoint compartido con **008**.
- Protección FE: `authGuard` (layout padre) + `engineerGuard` en ruta.

Spec **007** declara Out of Scope explorer. Spec **008** posee contrato principal de `GET /stats/loads`; **009** documenta uso contextual en explorer. Esta spec cierra la brecha SDD de **inspección read-only warehouse**.

---

## Problema

### Situación actual

Data engineers necesitan:

1. **Listar** tablas warehouse con metadatos (nombre, tipo, capa, row_count, columnas).
2. **Filtrar** tablas por nombre en UI.
3. **Previsualizar** filas paginadas de una tabla seleccionada.
4. **Ver** esquema columnas y consulta SQL asociada al preview.
5. **Consultar** conteos por tipo (dimensión, hecho, agregación) en KPIs.
6. **Revisar** historial reciente de cargas ELT junto a la exploración.
7. **Acceder** solo con rol engineer autenticado.

Riesgos sin especificación formal:

- Explorer APIs sin CU/FR/RB auditables (deuda P11: sin auth backend).
- Overlap `GET /stats/loads` con **008** sin delimitación.
- Riesgo de asumir SQL editor libre o export (ausentes en código).
- Whitelist table names parcialmente implementada pero sin reglas documentadas.

### Problema de negocio

**Voxmetriks no puede gobernar la inspección warehouse** si la UI explorer — punto de acceso a datos crudos para engineers — carece de reglas empresariales read-only, trazabilidad OE→HU y delimitación frente a pipeline (**008**) y analítica (**007**).

---

## Objetivo

Gobernar la **capacidad operativa de Explorador de Datos Warehouse**:

1. Exponer APIs explorer tables y preview documentadas.
2. Proveer UI `/explorer` protegida por engineer con navegación, filtro, preview paginado y esquema.
3. Mostrar SQL retornado por API (representación del preview, no ejecución ad-hoc).
4. Integrar panel historial cargas vía `GET /stats/loads` (delimitación **008**).
5. Garantizar operación read-only sin mutaciones warehouse desde explorer.
6. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU→FR→CA completa.

**Resultado esperado:** engineer autenticado inspecciona warehouse con UX predecible, datos paginados, estados vacío/error claros, sin capacidades inventadas (export, SQL libre, RBAC backend).

---

## Alcance (Scope)

### In Scope (evidencia implementada)

- Listado tablas warehouse con metadatos y clasificación `kind`.
- Preview paginado read-only con parámetros `page` y `limit`.
- Filtro búsqueda tablas client-side.
- KPIs conteo por tipo (dimension, fact, aggregation, total).
- Visualización esquema columnas y SQL query del preview.
- Panel historial cargas (`getLastLoads(10)`).
- Ruta `/explorer` con guards; entrada nav engineer.
- Estados loading, empty y error.

### In Scope parcial (documentado como deuda / limitación)

- Seguridad: whitelist nombres tabla en backend; **sin** auth backend en endpoints explorer (P11 deuda).
- Clasificación `control`, `application`, `other` en sidebar pero no en KPI cards principales.

### Out of Scope

Ver sección **Out of Scope** al final.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma que unifica experiencia musical con analítica de datos gobernada |
| **OT-09** | Objetivo Táctico | Habilitar inspección read-only del warehouse para operaciones de datos |
| **OO-14** | Objetivo Operativo | Operar explorador warehouse: tablas, preview paginado e historial cargas contextual para rol engineer |
| **M-14A** | Meta | Página `/explorer` carga tablas iniciales ≤ 4 s p95 con warehouse poblado |
| **M-14B** | Meta | 100 % accesos `/explorer` bloqueados para usuarios sin rol engineer (frontend) |
| **M-14C** | Meta | 100 % solicitudes preview con `table_name` inválido retornan HTTP 404 |
| **M-14D** | Meta | 0 mutaciones warehouse desde operaciones explorer (read-only) |
| **DEP-05** | Departamento | **Ingeniería de Datos** |
| **PKG-07** | Paquete | `data-engineering` (frontend `packages/data-engineering/explorer/`; backend `packages/analytics/routes/analytics.py` — explorer endpoints; servicio `analytics_service.py`) |

---

## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12) — filas 009 pendientes integración post-ratificación.

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-DE01 | US-DE01 | FR-DE01 | CA-001 |
| CU-DE01 | US-DE01 | FR-DE03 | CA-001 |
| CU-DE01 | US-DE01 | FR-DE13 | CA-001 |
| CU-DE01 | US-DE01 | FR-DE14 | CA-001 |
| CU-DE02 | US-DE01 | FR-DE09 | CA-002 |
| CU-DE05 | US-DE01 | FR-DE15 | CA-003 |
| CU-DE03 | US-DE02 | FR-DE02 | CA-004 |
| CU-DE03 | US-DE02 | FR-DE04 | CA-004 |
| CU-DE03 | US-DE02 | FR-DE12 | CA-005 |
| CU-DE03 | US-DE02 | FR-DE11 | CA-005 |
| CU-DE04 | US-DE02 | FR-DE06 | CA-006 |
| CU-DE04 | US-DE02 | FR-DE10 | CA-006 |
| CU-DE05 | US-DE02 | FR-DE07 | CA-005 |
| CU-DE06 | US-DE03 | FR-DE16 | CA-007 |
| CU-DE07 | US-DE04 | FR-DE08 | CA-008 |
| CU-DE07 | US-DE04 | FR-DE18 | CA-008 |
| CU-DE07 | US-DE04 | FR-DE17 | CA-009 |
| CU-DE01 | US-DE04 | FR-DE19 | CA-009 |
| CU-DE03 | US-DE04 | FR-DE21 | CA-009 |
| CU-DE03 | US-DE02 | FR-DE05 | CA-010 |

### Matriz de trazabilidad operativa (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE01 | US-DE01 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE02 | US-DE01 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE05 | US-DE01 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE04 | US-DE02 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14C | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE06 | US-DE03 | 009 | Implementado |
| OE-01 | OT-09 | OO-14 | M-14B | DEP-05 | PKG-07 | CU-DE07 | US-DE04 | 009 | Implementado |

---

## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Engineer** | Usuario autenticado con rol engineer (001 RB-015) | Inspeccionar tablas y filas warehouse read-only |
| **Sistema Voxmetriks** | Sirve APIs explorer; renderiza preview paginado | Cumplir P6 read-only; M-14A–D |
| **Capa Warehouse DuckDB** | Tablas schema `main` (dim_*, fact_*, agg_*, ctl_*, etc.) | Fuente inspeccionada |

---

## Casos de Uso

### CU-DE01: Abrir explorador y listar tablas warehouse

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE01 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Sesión válida; rol engineer; warehouse accesible |
| **Flujo principal** | 1. Engineer navega a `/explorer` → 2. Sistema aplica `authGuard` + `engineerGuard` → 3. UI solicita `GET /analytics/explorer/tables` → 4. UI renderiza KPIs kindCounts y sidebar tablas → 5. Si hay tablas, auto-selecciona primera y carga preview |
| **Postcondición** | Listado tablas visible o estado error |
| **Flujo alternativo** | 3a. API falla → `hasError=true`, loading false |
| **Flujo alternativo** | 5a. Lista vacía → sin preview activo |
| **Reglas de negocio** | RB-DE01, RB-DE03 |

### CU-DE02: Filtrar tablas por nombre

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE02 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | CU-DE01 completado; tablas cargadas |
| **Flujo principal** | 1. Engineer escribe en campo búsqueda sidebar → 2. UI filtra client-side por `name` contains (case insensitive) → 3. Lista sidebar muestra subconjunto |
| **Postcondición** | Tablas filtradas visibles; selección previa puede permanecer |
| **Reglas de negocio** | RB-DE04 |

### CU-DE03: Seleccionar tabla y previsualizar filas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE03 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Tablas listadas |
| **Flujo principal** | 1. Engineer selecciona tabla en sidebar → 2. UI resetea page=1 → 3. Sistema solicita `GET /analytics/explorer/preview/{table_name}` → 4. UI muestra metadatos tabla, esquema, SQL query, tabla filas |
| **Postcondición** | Preview visible o vacío tras error |
| **Flujo alternativo** | 3a. table_name inválido → API 404; preview null |
| **Reglas de negocio** | RB-DE02, RB-DE05, RB-DE06 |

### CU-DE04: Paginar preview de datos

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE04 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | CU-DE03; preview cargado |
| **Flujo principal** | 1. Engineer pulsa Anterior/Siguiente → 2. UI valida rango page 1..totalPages → 3. Sistema solicita preview con nuevo `page` (limit=8 default UI) → 4. UI actualiza filas y SQL query |
| **Postcondición** | Página correcta visible |
| **Flujo alternativo** | 2a. page fuera de rango → acción ignorada |
| **Reglas de negocio** | RB-DE02 |

### CU-DE05: Visualizar clasificación y conteos por tipo

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE05 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Tablas cargadas |
| **Flujo principal** | 1. Sistema clasifica cada tabla server-side (`kind`, `layer`) → 2. UI muestra badges kind en sidebar → 3. KPI cards muestran totales dimension/fact/aggregation/total |
| **Postcondición** | Conteos coherentes con listado |
| **Nota** | KPI cards no incluyen control/application/other (evidencia `kindCounts` L54–59) |
| **Reglas de negocio** | RB-DE07 |

### CU-DE06: Consultar historial cargas ELT en explorer

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE06 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Sesión engineer |
| **Flujo principal** | 1. En init UI solicita `GET /stats/loads?limit=10` → 2. Panel inferior muestra id, fecha, modo, registros_nuevos, total_raw, estado |
| **Postcondición** | Historial visible, vacío o error |
| **Delimitación** | Endpoint propiedad funcional **008**; explorer consume contextualmente |
| **Reglas de negocio** | RB-DE08 |

### CU-DE07: Acceder a ruta explorer (engineer)

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-DE07 |
| **Actor principal** | Usuario Engineer / Sistema |
| **Precondición** | Shell autenticado |
| **Flujo principal** | 1. Usuario engineer ve entrada nav `/explorer` → 2. Navegación permitida → 3. Usuario no engineer bloqueado por `engineerGuard` |
| **Postcondición** | Acceso FE acorde rol |
| **Reglas de negocio** | RB-DE01, RB-DE09 |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-DE01 — Navegar tablas warehouse (Priority: P1)

Como **Usuario Engineer**, quiero **listar y filtrar tablas del warehouse con KPIs por tipo**, para **orientarme en el esquema antes de inspeccionar filas**.

**Why this priority**: Entregable central OO-14; sidebar + KPIs son primera impresión; materializa M-14A.

**Independent Test**: Engineer abre `/explorer`; ≥1 tabla listada cuando warehouse poblado; KPI total > 0; filtro reduce lista.

**Acceptance Scenarios**:

1. **Given** warehouse con tablas, **When** explorer carga, **Then** sidebar lista tablas con name, kind badge, row_count (FR-DE01, FR-DE03).
2. **Given** tablas cargadas, **When** engineer filtra por texto, **Then** sidebar muestra solo coincidencias (FR-DE09).
3. **Given** tablas cargadas, **When** KPI grid renderiza, **Then** muestra total, dimensiones, hechos, agregaciones (FR-DE13, FR-DE15).
4. **Given** ≥1 tabla, **When** init completa, **Then** auto-selecciona primera tabla (FR-DE14).

**Maps to**: CU-DE01, CU-DE02, CU-DE05 | FR-DE01, FR-DE03, FR-DE09, FR-DE13–FR-DE15 | M-14A

---

### User Story US-DE02 — Preview paginado read-only (Priority: P1)

Como **Usuario Engineer**, quiero **inspeccionar filas, esquema y SQL del preview paginado**, para **validar contenido warehouse sin mutar datos**.

**Why this priority**: Core value explorer; cumple M-14D read-only.

**Independent Test**: Seleccionar tabla; preview 8 filas; paginar; SQL visible; 404 en tabla inválida vía API.

**Acceptance Scenarios**:

1. **Given** tabla seleccionada, **When** preview carga, **Then** muestra columnas, filas, total, page, limit (FR-DE02, FR-DE04).
2. **Given** preview activo, **When** engineer pagina, **Then** solicita nueva page con limit=8 (FR-DE06, FR-DE10).
3. **Given** metadatos tabla, **When** panel renderiza, **Then** esquema columnas name/type visible (FR-DE11, FR-DE12).
4. **Given** respuesta preview, **When** UI muestra SQL, **Then** texto proviene de campo `query` API (FR-DE07).
5. **Given** table_name inexistente, **When** API preview, **Then** HTTP 404 (FR-DE05, M-14C).

**Maps to**: CU-DE03, CU-DE04 | FR-DE02, FR-DE04–FR-DE07, FR-DE10–FR-DE12 | M-14C, M-14D

---

### User Story US-DE03 — Panel historial cargas (Priority: P1)

Como **Usuario Engineer**, quiero **ver historial reciente de cargas ELT en la página explorer**, para **contextualizar exploración con operaciones pipeline**.

**Why this priority**: Evidencia panel loads; complementa **008** sin duplicar spec.

**Independent Test**: Panel muestra hasta 10 cargas desde `/stats/loads`; empty state si sin registros.

**Acceptance Scenarios**:

1. **Given** ctl_carga_dataset con filas, **When** explorer init, **Then** panel loads muestra columnas id, fecha, modo, registros_nuevos, total_raw, estado (FR-DE16).
2. **Given** sin cargas, **When** API loads vacío, **Then** mensaje empty (FR-DE17).
3. **Given** loads API falla, **When** init, **Then** mensaje error conectividad (FR-DE17).

**Maps to**: CU-DE06 | FR-DE16, FR-DE17 | Delimitación **008**

---

### User Story US-DE04 — Acceso engineer y robustez (Priority: P1)

Como **Sistema Voxmetriks**, debo **restringir explorer a engineers y degradar ante errores API**, para **cumplir M-14B y UX operativa**.

**Why this priority**: Transversal seguridad FE y estados error.

**Independent Test**: Usuario estándar bloqueado; engineer ve nav; API tables fail → hasError sin crash.

**Acceptance Scenarios**:

1. **Given** usuario sin engineer, **When** navega `/explorer`, **Then** engineerGuard bloquea (FR-DE08, M-14B).
2. **Given** engineer autenticado, **When** shell carga, **Then** nav incluye explorador (FR-DE18).
3. **Given** explorer tables API falla, **When** init, **Then** hasError y mensaje degradado (FR-DE17, FR-DE19).
4. **Given** operación explorer, **When** APIs procesan, **Then** zero mutaciones warehouse (FR-DE21, M-14D).

**Maps to**: CU-DE07, CU-DE01 | FR-DE08, FR-DE17–FR-DE19, FR-DE21 | M-14B, M-14D

---

### Edge Cases

- **Warehouse sin tablas**: sidebar vacío; KPIs en cero; sin preview activo.
- **Tabla con 0 filas**: preview total=0; paginación 1 página.
- **Tabla con >8 columnas**: SQL display lista primeras 8 columnas en query string (evidencia backend L321).
- **Filtro sin coincidencias**: sidebar vacío; selección puede quedar en tabla no visible.
- **Cambio tabla mid-fetch**: nueva selección dispara nuevo preview (plan: cancelación).
- **Valores null en celdas**: UI muestra em dash `—` (cellValue).
- **Estado loads `estado` distinto de `ok`**: UI aplica clase error (evidencia HTML status-err).
- **Preview limit API max 50**: UI usa 8 fijo; API acepta 1–50 si invocado directamente.

---

## Requirements *(mandatory)*

### Functional Requirements — API Explorer

- **FR-DE01**: System MUST expose `GET /api/v1/analytics/explorer/tables` returning array of warehouse table metadata from schema `main`.
- **FR-DE02**: System MUST expose `GET /api/v1/analytics/explorer/preview/{table_name}` accepting query params `page` (≥1) and `limit` (1–50) returning paginated row preview.
- **FR-DE03**: Each table metadata entry MUST include `name`, `kind`, `layer`, `row_count`, `columns` (array of `{name, type}`).
- **FR-DE04**: Preview response MUST include `table`, `total`, `page`, `limit`, `columns`, `rows`, `query`.
- **FR-DE05**: Preview MUST return HTTP 404 when `table_name` is not in allowed tables set (whitelist via `information_schema.tables`).
- **FR-DE06**: Preview MUST execute paginated read `SELECT * FROM "{table_name}" LIMIT ? OFFSET ?` without mutating data.
- **FR-DE07**: Preview response `query` MUST reflect SELECT with column list (up to first 8 columns), LIMIT and OFFSET matching request.

### Functional Requirements — API Clasificación server-side

- **FR-DE12**: System MUST classify table `kind` by name prefix: `dim_`→dimension, `fact_`→fact, `agg_`→aggregation, `ctl_`/ `raw_spotify`→control, `app_`→application, else other.
- **FR-DE20**: System MUST set `layer` to `gold` when kind is dimension, fact, or aggregation; otherwise `warehouse`.

### Functional Requirements — API Loads (delimitación 008)

- **FR-DE16**: Explorer UI MUST call `GET /api/v1/stats/loads` with `limit=10` for ELT load history panel; contract owned by spec **008** (FR-PM03).

### Functional Requirements — UI Explorer

- **FR-DE08**: UI MUST provide route `/explorer` protected by parent `authGuard` and route `engineerGuard`.
- **FR-DE09**: UI MUST filter table list client-side by search string matching table `name` (case insensitive).
- **FR-DE10**: UI MUST paginate preview with default `pageSize=8` and Anterior/Siguiente controls bounded by `totalPages`.
- **FR-DE11**: UI MUST display schema grid from selected table metadata columns.
- **FR-DE13**: UI MUST display KPI cards for total tables, dimension count, fact count, aggregation count derived from loaded tables.
- **FR-DE14**: UI MUST auto-select first table and load preview page 1 when tables load successfully.
- **FR-DE15**: UI MUST display kind badges with localized labels (Dimensión, Hecho, Agregación, Control, App, Otro) in sidebar.
- **FR-DE17**: UI MUST show loading skeletons/states for tables, preview, and loads; MUST show empty and error messages when API fails or returns no data.
- **FR-DE18**: Engineer shell navigation MUST include entry to `/explorer`.
- **FR-DE19**: UI MUST set `hasError` on tables or loads fetch failure without uncaught exceptions.

### Functional Requirements — Read-only

- **FR-DE21**: Explorer feature MUST NOT expose UI or API operations that INSERT, UPDATE, or DELETE warehouse table data.

---

## Non-Functional Requirements

- **NFR-DE01 (Performance)**: `/explorer` initial tables load MUST complete ≤ 4 s p95 when warehouse populated locally (M-14A).
- **NFR-DE02 (Performance)**: Preview page fetch MUST complete ≤ 2 s p95 for tables ≤ 1M rows with limit=8.
- **NFR-DE03 (UX)**: Explorer MUST show distinct loading indicators for tables list, preview, and loads panel.
- **NFR-DE04 (Reliability)**: API errors MUST surface as recoverable UI states (empty, error message), not white screen.
- **NFR-DE05 (Data integrity — P6)**: Explorer operations MUST be read-only; no warehouse mutations (M-14D).
- **NFR-DE06 (Security — current state)**: Explorer endpoints documented as **without server-side engineer authentication** (deuda P11; RB-DE09).
- **NFR-DE07 (Security)**: Table name validation MUST use whitelist from `information_schema` before executing preview query (Constitución SQL injection guidance).
- **NFR-DE08 (i18n)**: Explorer nav label MUST support ES/EN via `nav.explorer` key.
- **NFR-DE09 (Maintainability)**: Feature MUST maintain traceability matrix CU→FR→CA documented in this spec.
- **NFR-DE10 (Auditability)**: Preview SQL displayed MUST correspond to server-executed query representation, not client-invented ad-hoc SQL.

---

## Reglas de Negocio

- **RB-DE01**: Route `/explorer` MUST require authenticated engineer role on frontend (`engineerGuard` per **001** RB-015).
- **RB-DE02**: Preview MUST only query tables present in warehouse `information_schema.tables` whitelist.
- **RB-DE03**: Explorer MUST NOT mutate warehouse data (read-only inspection).
- **RB-DE04**: Table search filter MUST operate client-side on already-fetched table list without additional API calls.
- **RB-DE05**: Invalid table preview requests MUST fail with HTTP 404, not execute arbitrary SQL.
- **RB-DE06**: Displayed SQL in UI MUST be sourced from API response field `query`; users MUST NOT execute custom SQL from explorer UI (no SQL editor).
- **RB-DE07**: KPI kind counts MUST include dimension, fact, aggregation, and total only — control/application/other appear in sidebar badges but not KPI cards (estado actual).
- **RB-DE08**: Load history panel MUST use `GET /stats/loads`; primary spec ownership is **008** (RB-PM12).
- **RB-DE09**: Endpoints `/analytics/explorer/*` are accessible without server-side auth in current code (documented P11 debt).
- **RB-DE10**: Explorer MUST NOT provide export CSV/JSON/download of preview data (capability absent).
- **RB-DE11**: Pagination MUST reset to page 1 when engineer selects a different table.

---

## Criterios de Aceptación Globales

1. **CA-001**: Engineer abre `/explorer` y ve listado tablas + KPIs + auto-preview primera tabla (CU-DE01).
2. **CA-002**: Filtro sidebar reduce tablas visibles sin llamada API adicional (CU-DE02).
3. **CA-003**: KPI cards muestran conteos dimension/fact/aggregation/total (CU-DE05).
4. **CA-004**: Selección tabla carga preview paginado con metadatos (CU-DE03).
5. **CA-005**: Esquema columnas y SQL query visibles en panel preview (CU-DE03).
6. **CA-006**: Paginación Anterior/Siguiente respeta totalPages (CU-DE04).
7. **CA-007**: Panel loads muestra hasta 10 registros ctl_carga_dataset o empty (CU-DE06).
8. **CA-008**: Usuario no engineer bloqueado en `/explorer` (CU-DE07, M-14B).
9. **CA-009**: Fallo API tables/loads muestra error degradado sin crash SPA (FR-DE17).
10. **CA-010**: Preview table_name inválido retorna 404 API (FR-DE05, M-14C).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-DE01**: 95% cargas iniciales `/explorer` (tablas + loads parallel) completan ≤ 4 s p95 con warehouse demo poblado (M-14A).
- **SC-DE02**: 100% intentos acceso `/explorer` por usuario no engineer bloqueados en frontend (M-14B).
- **SC-DE03**: 100% requests preview con table_name no whitelisted retornan HTTP 404 (M-14C).
- **SC-DE04**: 0 mutaciones warehouse en suite pruebas explorer APIs (M-14D).
- **SC-DE05**: 100% filas preview limitadas a parámetro `limit` (default UI 8).
- **SC-DE06**: 100% filas matriz CU→FR→CA en spec 009 listas para TRACEABILITY-MASTER post-ratificación OT-09/OO-14.

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-DE01 | Explorer APIs sin auth backend (P11) | Alta | Alto | RB-DE09, NFR-DE06; Out of Scope RBAC BE |
| R-DE02 | Overlap GET loads con spec 008 | Media | Bajo | RB-DE08, FR-DE16 delimitación |
| R-DE03 | Usuario asume SQL editor libre | Media | Alto | RB-DE06, Out of Scope SQL ad-hoc |
| R-DE04 | Usuario asume export disponible | Media | Medio | RB-DE10, Out of Scope export |
| R-DE05 | KPI counts omiten control/app tables | Baja | Bajo | RB-DE07 documentado |
| R-DE06 | Preview en tabla grande lento | Media | Medio | NFR-DE02; limit=8 |
| R-DE07 | Filtro oculta tabla seleccionada | Baja | Bajo | Edge case documentado |
| R-DE08 | Confusión explorer vs 008 warehouse status | Media | Medio | Out of Scope GET /analytics/warehouse en 009 |
| R-DE09 | SQL display parcial (8 cols) malinterpretado | Baja | Bajo | FR-DE07, edge case |
| R-DE10 | StatsService mezcla métodos sin frontera | Media | Medio | PKG-07; delimitar métodos explorer vs 007/008 |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| `001-user-identity-access` | Hard | Sesión, authGuard, engineerGuard, RB-015 |
| `008-pipeline-monitoring` | Soft | Contrato `GET /stats/loads`; ctl_carga_dataset poblado por pipeline/synthetic |
| Warehouse DuckDB schema `main` | Hard | Tablas inspeccionables |
| `StatsService` | Hard | getExplorerTables, getTablePreview, getLastLoads |
| `ExplorerComponent` | Hard | UI `/explorer` |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | P2 PKG-07, P6 read-only, P11 deuda auth, §12 trazabilidad |
| `SPEC-008-011-EVIDENCE-AUDIT.md` | Evidencia única autorizada alcance 009 |
| `007-operational-analytics-dashboards/spec.md` | Out of Scope explorer |
| `008-pipeline-monitoring/spec.md` | Propiedad loads endpoint |

### Dependencias externas

| Dependencia | Descripción |
|-------------|-------------|
| DuckDB file | `data/warehouse/voxmetrik.duckdb` |
| FastAPI operativo | Endpoints analytics explorer |

### Specs relacionadas

| Spec | Relación |
|------|----------|
| `008-pipeline-monitoring` | Loads panel; pipeline alimenta tablas exploradas |
| `007-operational-analytics-dashboards` | Analítica consumo independiente de explorer |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§3.1 In Scope** | Explorer warehouse explícitamente incluido |
| **§4.3 Nivel Operativo** | Inspección warehouse día a día engineer |
| **§5 P2 Package-by-Domain** | PKG-07 data-engineering |
| **§5 P6 Warehouse vs App** | NFR-DE05 read-only inspection |
| **§5 P11 Security mutations** | RB-DE09 deuda auth explorer APIs |
| **§12 Trazabilidad** | Matriz OE→Impl en spec |
| **§14 Nomenclatura** | Branch `009-data-explorer` |
| **SQL injection guidance** | NFR-DE07 whitelist table names |

---

## Out of Scope

- SQL editor libre / ejecución consultas ad-hoc desde UI.
- Export CSV/JSON/download de preview.
- Mutaciones warehouse desde explorer (INSERT/UPDATE/DELETE).
- RBAC engineer en backend para `/analytics/explorer/*` (no implementado).
- Linaje visual entre tablas (diagrama).
- Filtros columnares en preview.
- Integración `ctl_auditoria` en UI explorer.
- `GET /analytics/warehouse` en página explorer (no invocado en código).
- Pipeline synthetic / ELT UI (**008**).
- Dashboards analíticos consumo (**007**).
- CRUD steward (**010**).
- Health/metadata (**011** / **006**).
- WebSocket / realtime preview updates.
- PocketBase ingest UI.

---

## Assumptions

- Warehouse contiene al menos una tabla en schema `main` tras ELT para demo útil.
- `ctl_carga_dataset` puede estar vacío — panel loads muestra empty state aceptable.
- Rol engineer determinado por **001** (`AuthService.hasEngineerAccess()`).
- `environment.apiUrl` apunta a API con prefijo `/api/v1`.
- Preview default UI pageSize 8 alineado con backend default limit=8.
- FastAPI disponible en entorno dev (mensaje error referencia localhost:8000 en UI).
- Idiomas ES/EN suficientes para labels explorer y nav.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — evidencia `SPEC-008-011-EVIDENCE-AUDIT.md`  
**Next Step**: `/speckit-checklist` → `/speckit-plan` — Constitution Check P6, P11; delimitación contracts con 008.
