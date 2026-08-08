> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Monitoreo de Pipeline y Operaciones Sintéticas

**Feature Branch**: `008-pipeline-monitoring`  
**Feature Directory**: `specs/008-pipeline-monitoring/`  
**Created**: 2026-06-20  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de monitoreo de pipeline de datos: estado warehouse, historial de cargas, generación sintética controlada, UI engineer de pipeline ELT (simulación visual + API synthetic), tabs engineer en settings, y ejecución medallion ELT vía CLI/Docker fuera de SPA.

**Prerrequisitos:** `001-user-identity-access` (sesión, `engineerGuard`, RB-015); warehouse DuckDB accesible; pipeline medallion ejecutado al menos una vez vía `docker compose` o CLI para datos base (`elt/pipelines/elt_pipeline.py`).

**Evidencia base:** `SPEC-008-011-EVIDENCE-AUDIT.md` v1.0.0 (2026-06-20). Esta spec **no** introduce capacidades ausentes en código.

**Delimitación vs otras specs (evitar duplicidad):**

| Dominio | Spec propietaria | Spec 008 |
|---------|------------------|----------|
| Auth / sesión / engineerGuard | 001 | ❌ Consume identidad y rol engineer FE |
| Perfil / settings core / health tab | 006 | ❌ Solo tabs warehouse/pipeline engineer (contenido 008) |
| Dashboards analíticos consumo BI | 007 | ❌ `GET /stats/summary` en ELT es **contexto KPI** únicamente |
| Explorer tablas warehouse | 009 | ❌ |
| CRUD steward catálogo | 010 | ❌ |
| Health / root metadata | 011 | ❌ |
| Recomendaciones / historial | 005 | ❌ |

**Delimitación crítica (evidencia código):** La acción **“Ejecutar pipeline”** en `/elt-pipeline` MUST interpretarse como **(a)** progresión visual simulada del flujo Medallion en UI y **(b)** única mutación real vía `POST /api/v1/stats/synthetic`. **NO** dispara `elt/pipelines/elt_pipeline.py` ni existe endpoint HTTP de orquestación ELT. El pipeline medallion completo MUST operarse vía servicio Docker `pipeline` o CLI (CU-PM08).

---

## Contexto Empresarial

Voxmetriks combina consumo musical con una capa analítica warehouse Medallion (Constitución §1–§2, P7 ELT-before-API). Los **data engineers** MUST poder **observar** el estado del warehouse, **consultar** historial de cargas, **generar** datos sintéticos acotados para demos/escala, y **operar** preferencias locales de pipeline — sin confundir simulación UI con ejecución ELT real.

La auditoría de evidencia (`SPEC-008-011-EVIDENCE-AUDIT.md`) confirmó implementación ~72 % sin spec dedicada:

- Ruta UI `/elt-pipeline` (`EltPipelineComponent`) con KPIs, timeline simulado, logs, generación synthetic.
- APIs: `GET /stats/loads`, `GET /stats/synthetic/limits`, `POST /stats/synthetic`, `GET /analytics/warehouse`.
- Control tables: `ctl_carga_dataset`, `ctl_pipeline_stages` (lectura).
- Pipeline medallion: `docker-compose.yml` servicio `pipeline` → `elt/pipelines/elt_pipeline.py` (fuera SPA).
- Settings engineer: tabs `warehouse` (listas estáticas) y `pipeline` (prefs `localStorage`).

Spec **007** declara Out of Scope pipeline/synthetic. Spec **006** declara visibilidad tabs engineer (FR-ST11) pero no contenido warehouse/pipeline. Esta spec cierra la brecha SDD de **monitoreo pipeline y operaciones sintéticas** — distinta de explorer (**009**) y analítica consumo (**007**).

---

## Problema

### Situación actual

Data engineers y DevOps necesitan:

1. **Visualizar** KPIs warehouse y última carga al abrir la consola pipeline.
2. **Consultar** estado de capas Medallion, KPIs warehouse y stages recientes desde API.
3. **Revisar** historial de cargas registradas en `ctl_carga_dataset`.
4. **Configurar** volumen synthetic (multiplicador o target custom) con validación previa.
5. **Ejecutar** generación synthetic acotada desde UI tras feedback visual de progreso.
6. **Acceder** a referencia warehouse/pipeline en settings (rol engineer).
7. **Ejecutar** pipeline medallion completo fuera de SPA (Docker/CLI).

Riesgos sin especificación formal:

- Usuarios interpretan timeline UI como ELT real remoto (evidencia: `runPipeline()` anima pasos; API real solo synthetic).
- POST synthetic y warehouse status sin CU/FR/RB auditables (deuda P11: sin auth backend).
- Overlap `StatsService.getSummary` con **007** sin delimitación.
- Settings `autoRefresh` sugiere refresh operativo pero no tiene consumidor en ELT (evidencia grep).
- Tab warehouse settings muestra listas hardcodeadas — riesgo de asumir datos live.

### Problema de negocio

**Voxmetriks no puede gobernar operaciones de datos demo/escala** si la UI pipeline — visible solo a engineers — carece de reglas empresariales que distingan **monitoreo**, **generación synthetic** y **ELT medallion CLI**, con trazabilidad OE→HU y límites P10 synthetic boundary.

---

## Objetivo

Gobernar la **capacidad operativa de Monitoreo de Pipeline y Operaciones Sintéticas**:

1. Exponer APIs de loads, limits, synthetic y warehouse status documentadas.
2. Proveer UI `/elt-pipeline` protegida por engineer con monitoreo, validación volumen y ejecución synthetic.
3. Documentar explícitamente que la timeline UI es **simulación visual**; mutación warehouse vía synthetic API únicamente en SPA.
4. Registrar cargas synthetic exitosas en `ctl_carga_dataset`.
5. Delimitar tabs engineer settings (contenido estático/local vs APIs live).
6. Documentar vía CU operativo la ejecución ELT medallion Docker/CLI.
7. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU→FR→CA completa.

**Resultado esperado:** engineer autenticado monitorea warehouse, ejecuta synthetic controlado, comprende límites y no confunde simulación UI con orquestación ELT remota.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma que unifica experiencia musical con analítica de datos gobernada |
| **OT-08** | Objetivo Táctico | Habilitar operaciones de datos: monitoreo pipeline, synthetic y ELT operativo |
| **OO-13** | Objetivo Operativo | Operar monitoreo pipeline, generación sintética acotada y referencia warehouse para rol engineer |
| **M-13A** | Meta | Página `/elt-pipeline` carga KPIs iniciales ≤ 4 s p95 con warehouse poblado |
| **M-13B** | Meta | 100 % accesos `/elt-pipeline` bloqueados para usuarios sin rol engineer (frontend) |
| **M-13C** | Meta | 100 % solicitudes synthetic fuera de límites rechazadas en UI antes de POST |
| **M-13D** | Meta | 100 % ejecuciones synthetic exitosas registran fila en `ctl_carga_dataset` |
| **DEP-05** | Departamento | **Ingeniería de Datos** |
| **PKG-07** | Paquete | `data-engineering` (frontend `packages/data-engineering/`; backend endpoints en `packages/analytics/routes/{stats,analytics}.py`; ELT `elt/pipelines/`) |

---

## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../README.md) (Constitución §12) — filas 008 pendientes integración post-ratificación.

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-PM01 | US-PM01 | FR-PM07 | CA-001 |
| CU-PM01 | US-PM01 | FR-PM08 | CA-001 |
| CU-PM01 | US-PM01 | FR-PM21 | CA-001 |
| CU-PM05 | US-PM01 | FR-PM04 | CA-002 |
| CU-PM05 | US-PM01 | FR-PM16 | CA-002 |
| CU-PM04 | US-PM04 | FR-PM03 | CA-003 |
| CU-PM06 | US-PM02 | FR-PM01 | CA-004 |
| CU-PM06 | US-PM02 | FR-PM09 | CA-004 |
| CU-PM02 | US-PM02 | FR-PM09 | CA-004 |
| CU-PM02 | US-PM02 | FR-PM10 | CA-004 |
| CU-PM03 | US-PM02 | FR-PM02 | CA-005 |
| CU-PM03 | US-PM02 | FR-PM12 | CA-005 |
| CU-PM03 | US-PM02 | FR-PM22 | CA-005 |
| CU-PM03 | US-PM03 | FR-PM11 | CA-006 |
| CU-PM03 | US-PM03 | FR-PM13 | CA-006 |
| CU-PM03 | US-PM03 | FR-PM14 | CA-005 |
| CU-PM03 | US-PM03 | FR-PM15 | CA-007 |
| CU-PM03 | US-PM06 | FR-PM17 | CA-008 |
| CU-PM07 | US-PM05 | FR-PM18 | CA-009 |
| CU-PM07 | US-PM05 | FR-PM19 | CA-009 |
| CU-PM07 | US-PM05 | FR-PM20 | CA-010 |
| CU-PM01 | US-PM06 | FR-PM05 | CA-011 |
| CU-PM01 | US-PM06 | FR-PM06 | CA-011 |
| CU-PM01 | US-PM06 | FR-PM23 | CA-011 |
| CU-PM01 | US-PM06 | FR-PM25 | CA-011 |
| CU-PM08 | US-PM07 | FR-PM24 | CA-012 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM01 | US-PM01 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM05 | US-PM01 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM02 | US-PM02 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM06 | US-PM02 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM02 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM03 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM04 | US-PM04 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM01 | US-PM06 | 008 | Implementado |
| OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM07 | US-PM05 | 008 | Parcial |
| OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM08 | US-PM07 | 008 | Implementado |

---

## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Engineer** | Usuario autenticado con rol engineer (001 RB-015) | Monitorear pipeline; ejecutar synthetic; acceder settings data ops |
| **DevOps / Operador de Plataforma** | Ejecuta ELT medallion vía Docker/CLI | Poblar warehouse antes de operaciones SPA |
| **Sistema Voxmetriks** | Sirve APIs pipeline; persiste ctl_*; renderiza simulación UI | Cumplir P7, P10; registrar cargas |
| **Capa Warehouse DuckDB** | dim_track, ctl_carga_dataset, ctl_pipeline_stages | Fuente de verdad monitoreo |

---

## Casos de Uso

### CU-PM01: Abrir consola pipeline ELT y cargar KPIs

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM01 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Sesión válida; rol engineer; API accesible |
| **Flujo principal** | 1. Engineer navega a `/elt-pipeline` → 2. Sistema aplica `authGuard` + `engineerGuard` → 3. UI solicita limits, summary (contexto), last load (1), warehouse status → 4. KPIs y estado conexión visibles |
| **Postcondición** | Panel pipeline cargado o error degradado por endpoint |
| **Flujo alternativo** | 3a. API summary falla → `apiConnected=false`; resto endpoints intentan cargar |
| **Flujo alternativo** | 2a. Usuario sin engineer → redirect/bloqueo guard |
| **Reglas de negocio** | RB-PM03, RB-PM11 |

### CU-PM02: Configurar volumen generación synthetic

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM02 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | CU-PM01; limits cargados |
| **Flujo principal** | 1. Engineer selecciona modo multiplier (1×–4×) o custom target → 2. UI calcula objetivo de eventos, delta de actividad y estimación MB → 3. `volumeValidation` evalúa contra limits → 4. Botón ejecutar habilitado/deshabilitado según validación |
| **Postcondición** | Configuración volumen lista o mensaje error/info |
| **Flujo alternativo** | 3a. Target > max_target_total → error, run deshabilitado |
| **Flujo alternativo** | 3a. Delta > max_create_per_run → error, run deshabilitado |
| **Flujo alternativo** | 3a. Delta = 0 → info “objetivo cubierto”, run deshabilitado |
| **Reglas de negocio** | RB-PM04, RB-PM05 |

### CU-PM03: Ejecutar flujo UI pipeline (simulación + synthetic)

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM03 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | CU-PM02 válido; `canRunPipeline=true` |
| **Flujo principal** | 1. Engineer pulsa ejecutar → 2. UI importa catálogo real PocketBase → 3. UI invoca `POST /stats/synthetic` con `target_total` de eventos → 4. API genera actividad sintética (streams, búsquedas, favoritos, playlists, sesiones) sobre tracks reales y registra ctl_carga_dataset → 5. UI actualiza summary, last load, estado completed |
| **Postcondición** | Catálogo musical permanece real; facts de actividad expandidos; registro carga; logs SUCCESS |
| **Flujo alternativo** | 3a. POST falla → estado `failed`, log WARN con detail API |
| **Flujo alternativo** | 3a. Delta=0 antes POST → complete sin API |
| **Reglas de negocio** | RB-PM01, RB-PM02, RB-PM05, RB-PM09 |

### CU-PM04: Consultar historial de cargas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM04 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Sesión engineer |
| **Flujo principal** | 1. Sistema solicita `GET /stats/loads` → 2. UI presenta registros (fecha, modo, registros_nuevos, total_raw, estado) |
| **Postcondición** | Historial visible o vacío |
| **Nota** | Mismo endpoint usado en explorer (**009**) — delimitación panel contextual |
| **Reglas de negocio** | RB-PM12 |

### CU-PM05: Consultar estado warehouse y capas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM05 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Warehouse accesible |
| **Flujo principal** | 1. Sistema solicita `GET /analytics/warehouse` → 2. UI muestra pipeline_status, db_size_mb, layers (bronze/silver/gold), kpis, recent_stages, last_load |
| **Postcondición** | Estado warehouse visible |
| **Flujo alternativo** | 2a. ctl_pipeline_stages ausente → recent_stages vacío sin error fatal |
| **Reglas de negocio** | RB-PM09 |

### CU-PM06: Consultar límites synthetic

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM06 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | API operativa |
| **Flujo principal** | 1. Sistema solicita `GET /stats/synthetic/limits` → 2. UI expone max_target_total, max_create_per_run, warn_create_above, batch_size, duckdb_note |
| **Postcondición** | Limits disponibles para validación CU-PM02 |
| **Flujo alternativo** | 1a. API falla → UI usa defaults client-side documentados en código |
| **Reglas de negocio** | RB-PM04 |

### CU-PM07: Acceder tabs warehouse/pipeline en settings

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM07 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Sesión engineer; en `/settings` |
| **Flujo principal** | 1. Settings filtra tabs visibles (engineerTabs) → 2. Engineer abre tab warehouse → ve path fijo y listas goldTables/aggregations estáticas → 3. Engineer abre tab pipeline → configura defaultRecords, loadMode, autoRefresh → 4. Prefs persisten en localStorage vía UiPreferencesService |
| **Postcondición** | Tabs visibles solo engineer; prefs guardadas localmente |
| **Delimitación** | Visibilidad tabs: **006** FR-ST11; contenido tabs: **008** |
| **Reglas de negocio** | RB-PM06, RB-PM07, RB-PM08 |

### CU-PM08: Ejecutar pipeline medallion ELT (CLI/Docker)

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PM08 |
| **Actor principal** | DevOps / Operador de Plataforma |
| **Precondición** | Entorno Docker o Python ELT; datos fuente disponibles |
| **Flujo principal** | 1. Operador ejecuta servicio `pipeline` en docker-compose o `elt/pipelines/elt_pipeline.py` → 2. Pipeline procesa capas Medallion → 3. Warehouse y ctl_* actualizados → 4. Servicio API puede arrancar tras pipeline (P7) |
| **Postcondición** | Warehouse poblado/actualizado fuera de SPA |
| **Nota** | **No** existe invocación desde UI `/elt-pipeline` |
| **Reglas de negocio** | RB-PM02, RB-PM01 |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-PM01 — Monitoreo KPIs y estado warehouse (Priority: P1)

Como **Usuario Engineer**, quiero **ver KPIs warehouse, última carga y estado de capas al abrir la consola pipeline**, para **situarme antes de operar synthetic**.

**Why this priority**: Entregable central OO-13; materializa M-13A; punto de entrada `/elt-pipeline`.

**Independent Test**: Engineer abre `/elt-pipeline`; ve KPIs summary, última carga, distribución tablas desde warehouse status; estados loading completan.

**Acceptance Scenarios**:

1. **Given** warehouse poblado y API OK, **When** engineer abre `/elt-pipeline`, **Then** carga limits, summary, last load (1), warehouse status (FR-PM07, FR-PM08, FR-PM04, FR-PM16).
2. **Given** warehouse status responde, **When** UI procesa layers gold, **Then** actualiza distribución dimensiones/facts/agregados (FR-PM16).
3. **Given** summary disponible, **When** KPIs renderizan, **Then** total_tracks coherente con warehouse kpis (FR-PM21 delimitación 007).

**Maps to**: CU-PM01, CU-PM05 | FR-PM04, FR-PM07, FR-PM08, FR-PM16, FR-PM21 | M-13A

---

### User Story US-PM02 — Generación synthetic controlada (Priority: P1)

Como **Usuario Engineer**, quiero **configurar volumen y ejecutar generación synthetic con validación previa**, para **escalar catálogo demo sin exceder límites**.

**Why this priority**: Única mutación warehouse vía SPA; cumple M-13C/M-13D y P10.

**Independent Test**: Seleccionar multiplier; validación OK; ejecutar; POST synthetic 200; ctl_carga_dataset nueva fila; total_tracks incrementado.

**Acceptance Scenarios**:

1. **Given** limits API, **When** engineer configura multiplier/custom, **Then** UI muestra target, delta y validación (FR-PM01, FR-PM09, FR-PM10).
2. **Given** validación error (excede max), **When** engineer intenta ejecutar, **Then** botón deshabilitado (FR-PM10, RB-PM04).
3. **Given** validación OK, **When** flujo UI completa pasos simulados, **Then** POST `/stats/synthetic` con target_total (FR-PM02, FR-PM12, FR-PM22).
4. **Given** POST exitoso, **When** respuesta incluye created/after, **Then** UI log SUCCESS y refresca last load (FR-PM14).

**Maps to**: CU-PM02, CU-PM03, CU-PM06 | FR-PM01–FR-PM02, FR-PM09–FR-PM10, FR-PM12, FR-PM14, FR-PM22 | M-13C, M-13D

---

### User Story US-PM03 — Timeline y logs de ejecución UI (Priority: P1)

Como **Usuario Engineer**, quiero **observar progreso visual Medallion y logs operativos durante la ejecución UI**, para **seguir el flujo aunque la orquestación real sea synthetic**.

**Why this priority**: Diferencia explícita simulación vs ELT real (RB-PM01); previene malentendido operativo.

**Independent Test**: Ejecutar pipeline UI; timeline progresa extract→warehouse; logs INFO/SUCCESS; estado running→completed; **no** llamada HTTP a elt_pipeline.

**Acceptance Scenarios**:

1. **Given** run iniciado, **When** timer avanza, **Then** timeline steps cambian idle/running/success (FR-PM11, RB-PM01).
2. **Given** run en curso, **When** eventos ocurren, **Then** logs append con niveles INFO/WARN/SUCCESS (FR-PM13).
3. **Given** run completado o fallido, **When** engineer pulsa reset, **Then** timeline y logs vuelven idle (FR-PM15).
4. **Given** POST synthetic falla, **When** error API, **Then** estado failed y log WARN con detail (FR-PM17).

**Maps to**: CU-PM03 | FR-PM11, FR-PM13, FR-PM15, FR-PM17 | RB-PM01

---

### User Story US-PM04 — Historial de cargas (Priority: P1)

Como **Usuario Engineer**, quiero **consultar historial reciente de cargas**, para **auditar ejecuciones synthetic y ELT previas**.

**Why this priority**: Evidencia ctl_carga_dataset; complementa monitoreo M-13D.

**Independent Test**: GET loads retorna array; UI ELT muestra última carga; tras synthetic exitoso historial actualizado.

**Acceptance Scenarios**:

1. **Given** ctl_carga_dataset con filas, **When** UI solicita loads, **Then** muestra fecha, modo, registros_nuevos, estado (FR-PM03).
2. **Given** limit parameter, **When** API recibe limit N (1–50), **Then** retorna hasta N registros ordenados id_carga DESC (FR-PM03).

**Maps to**: CU-PM04 | FR-PM03 | M-13D

---

### User Story US-PM05 — Settings engineer warehouse/pipeline (Priority: P2)

Como **Usuario Engineer**, quiero **ver referencia warehouse y preferencias pipeline en settings**, para **acceso rápido sin confundir con datos live/API**.

**Why this priority**: Parcialmente implementado (listas estáticas, prefs local); cierra CU-PM07 con delimitación honesta.

**Independent Test**: Engineer ve tabs warehouse/pipeline; usuario estándar no; cambiar loadMode persiste tras reload; warehouse tab no llama getWarehouseStatus.

**Acceptance Scenarios**:

1. **Given** engineer en settings, **When** carga tabs, **Then** warehouse y pipeline visibles (FR-PM20, alineado 006 FR-ST11).
2. **Given** tab warehouse, **When** renderiza, **Then** muestra path `data/warehouse/voxmetrik.duckdb` y listas estáticas goldTables/aggregations (FR-PM18, RB-PM07).
3. **Given** tab pipeline, **When** engineer cambia defaultRecords/loadMode/autoRefresh, **Then** UiPreferencesService persiste localStorage (FR-PM19, RB-PM06).
4. **Given** pref autoRefresh=true, **When** engineer opera ELT page, **Then** **no** refresh automático adicional ocurre (RB-PM08 — estado actual).

**Maps to**: CU-PM07 | FR-PM18, FR-PM19, FR-PM20 | Impl Parcial

---

### User Story US-PM06 — Acceso engineer y rutas (Priority: P1)

Como **Sistema Voxmetriks**, debo **restringir consola pipeline a engineers autenticados y manejar errores API**, para **cumplir M-13B y UX operativa**.

**Why this priority**: Transversal seguridad FE y robustez.

**Independent Test**: Usuario estándar no accede `/elt-pipeline`; `/etl-pipeline` redirige; API error no crash SPA.

**Acceptance Scenarios**:

1. **Given** usuario sin engineer, **When** navega `/elt-pipeline`, **Then** engineerGuard bloquea (FR-PM05, M-13B).
2. **Given** URL legacy, **When** navega `/etl-pipeline`, **Then** redirect `/elt-pipeline` (FR-PM06).
3. **Given** endpoint falla, **When** ELT page carga, **Then** degradación parcial sin white screen (FR-PM23, NFR-PM04).
4. **Given** engineer autenticado, **When** shell carga, **Then** nav incluye entrada pipeline (FR-PM25).

**Maps to**: CU-PM01 | FR-PM05, FR-PM06, FR-PM25, FR-PM23 | M-13B

---

### User Story US-PM07 — ELT medallion vía Docker/CLI (Priority: P2)

Como **DevOps**, quiero **ejecutar pipeline medallion fuera de SPA**, para **poblar warehouse antes de monitoreo y synthetic**.

**Why this priority**: P7 compose; RB-PM02; no es UI pero es operación pipeline verificada.

**Independent Test**: `docker compose up pipeline` ejecuta elt_pipeline.py; API depende de pipeline en compose.

**Acceptance Scenarios**:

1. **Given** docker-compose, **When** servicio pipeline completa, **Then** warehouse contiene capas gold esperadas (FR-PM24, P7).
2. **Given** operador, **When** ejecuta elt_pipeline.py manualmente, **Then** mismo resultado que servicio compose (CU-PM08).

**Maps to**: CU-PM08 | FR-PM24 | P7

---

### Edge Cases

- **Warehouse vacío (dim_track=0)**: POST synthetic retorna created=0; UI MUST informar sin crash.
- **limits API caída**: UI usa defaults client-side; engineer puede operar con validación local.
- **Concurrent run**: segundo click durante running MUST ignorarse (`canRunPipeline` false).
- **Component destroy mid-run**: timers MUST limpiarse (`ngOnDestroy`) — NFR-PM09.
- **Synthetic excede límites server-side**: API 400; UI failed state.
- **ctl_pipeline_stages vacío**: warehouse status OK con recent_stages [].
- **Usuario engineer pierde rol mid-session**: guard en próxima navegación.
- **Prefs pipeline no afectan synthetic target**: defaultRecords/loadMode sin binding a ELT component (RB-PM06).

---

## Requirements *(mandatory)*

### Functional Requirements — API Pipeline & Synthetic

- **FR-PM01**: System MUST expose `GET /api/v1/stats/synthetic/limits` returning `max_target_total`, `max_create_per_run`, `warn_create_above`, `batch_size`, `duckdb_note`.
- **FR-PM02**: System MUST expose `POST /api/v1/stats/synthetic` accepting JSON body with `target_total` OR `multiplier` (mutually required per validator); MUST return `before`, `after`, `created`, `target_total`, `source_rows`, `batches`, `warning`.
- **FR-PM03**: System MUST expose `GET /api/v1/stats/loads` with optional `limit` (1–50) returning rows from `ctl_carga_dataset` ordered by `id_carga` DESC with fields: `id_carga`, `fecha_carga`, `modo`, `registros_nuevos`, `total_raw`, `estado`.
- **FR-PM04**: System MUST expose `GET /api/v1/analytics/warehouse` returning `pipeline_status`, `db_size_mb`, `layers` (bronze, silver, gold), `kpis`, `last_load`, `recent_stages` (from `ctl_pipeline_stages` when present).
- **FR-PM22**: POST synthetic successful MUST insert registration row into `ctl_carga_dataset` documenting load mode and counts.

### Functional Requirements — API Contextual (delimitación 007)

- **FR-PM21**: UI `/elt-pipeline` MAY call `GET /api/v1/stats/summary` solely for contextual KPI display; contract owned by spec **007** (FR-AN01).

### Functional Requirements — UI ELT Pipeline

- **FR-PM05**: UI MUST provide route `/elt-pipeline` protected by `authGuard` and `engineerGuard`.
- **FR-PM06**: UI MUST redirect `/etl-pipeline` to `/elt-pipeline`.
- **FR-PM07**: On init, ELT page MUST fetch synthetic limits, summary (contextual), last loads (limit 1), and warehouse status.
- **FR-PM08**: UI MUST set loading state until parallel init requests complete or fail individually.
- **FR-PM09**: UI MUST support volume modes `multiplier` (presets 1×–4×) and `custom` target integer.
- **FR-PM10**: UI MUST disable run action when API disconnected, pipeline running, validation error, or delta zero (info level).
- **FR-PM11**: During run, UI MUST animate Medallion timeline steps (extract, bronze, silver, gold, warehouse) as **visual simulation** without HTTP invocation of ELT medallion script.
- **FR-PM12**: After simulated steps complete, UI MUST invoke POST `/stats/synthetic` with computed `target_total` when delta > 0.
- **FR-PM13**: UI MUST append operational logs with levels INFO, WARN, SUCCESS and timestamps during run.
- **FR-PM14**: After successful synthetic, UI MUST refresh last load from GET `/stats/loads` and update displayed track totals.
- **FR-PM15**: UI MUST provide reset action clearing timeline, logs, timers, and run state when not running.
- **FR-PM16**: UI MUST derive table distribution chart from warehouse status gold layer counts when available.
- **FR-PM17**: On synthetic API error, UI MUST set pipeline state `failed`, log WARN with API detail, and stop timers.
- **FR-PM23**: UI MUST degrade gracefully on partial API failures without uncaught exceptions (empty/fallback values permitted).

### Functional Requirements — Settings Engineer Tabs

- **FR-PM18**: Settings warehouse tab MUST display static `warehousePath`, `goldTables`, and `aggregations` reference lists without calling `GET /analytics/warehouse`.
- **FR-PM19**: Settings pipeline tab MUST persist `defaultRecords`, `loadMode`, `autoRefresh` via UiPreferencesService (localStorage key `voxmetrik_ui_prefs`).
- **FR-PM20**: Settings MUST show warehouse and pipeline tabs ONLY for engineer role (extends **006** FR-ST11 content scope).

### Functional Requirements — Navigation & Operations

- **FR-PM25**: Authenticated engineer shell navigation MUST include entry to `/elt-pipeline`.
- **FR-PM24**: Platform MUST support medallion ELT execution via Docker Compose service `pipeline` running `elt/pipelines/elt_pipeline.py` independent of SPA (P7).

---

## Non-Functional Requirements

- **NFR-PM01 (Performance)**: `/elt-pipeline` initial KPI load MUST complete ≤ 4 s p95 when warehouse populated and API local (M-13A).
- **NFR-PM02 (Performance)**: POST synthetic MUST process within server-side limits (`MAX_CREATE_PER_RUN`, batched inserts) without blocking API indefinitely beyond request timeout.
- **NFR-PM03 (UX)**: ELT page MUST show loading indicators during initial KPI fetch.
- **NFR-PM04 (Reliability)**: API errors MUST surface as recoverable UI states (failed pipeline, disconnected API flag).
- **NFR-PM05 (Data integrity — P10)**: Synthetic tracks MUST be distinguishable in warehouse from source rows per server insert rules (`nombre_track` synthetic pattern); UI MUST NOT present synthetic generation as user telemetry.
- **NFR-PM06 (Operations — P7)**: Docker compose MUST start pipeline service before API dependency where configured.
- **NFR-PM07 (i18n)**: Pipeline settings strings MUST support ES/EN via platform i18n keys (`settings.pipeline.*`).
- **NFR-PM08 (Maintainability)**: Feature MUST document CU→FR→CA matrix in this spec for TRACEABILITY-MASTER integration.
- **NFR-PM09 (Reliability)**: ELT component MUST clear interval timers on destroy to prevent leaks.
- **NFR-PM10 (Security — current state)**: Pipeline monitoring APIs documented as **without server-side engineer authentication** in current implementation (deuda P11; see R-PM03).

---

## Reglas de Negocio

- **RB-PM01**: UI pipeline run MUST be defined as visual Medallion simulation plus POST synthetic — **NOT** remote execution of `elt_pipeline.py`.
- **RB-PM02**: Full medallion ELT MUST execute only via Docker Compose service `pipeline` or direct CLI invocation (CU-PM08).
- **RB-PM03**: Route `/elt-pipeline` MUST require engineer role on frontend (`engineerGuard` per **001** RB-015).
- **RB-PM04**: Synthetic volume MUST validate against limits (`max_target_total`, `max_create_per_run`, `warn_create_above`) before POST in UI; server MUST re-validate on POST.
- **RB-PM05**: POST synthetic MUST NOT create fake tracks/artists/albums/genres; it MUST generate activity facts over the real catalog and may purge legacy `syn_%` track clones.
- **RB-PM06**: Settings pipeline preferences (`defaultRecords`, `loadMode`, `autoRefresh`) MUST NOT trigger ELT or synthetic APIs automatically in current implementation.
- **RB-PM07**: Settings warehouse tab content MUST be treated as static operational reference, not live warehouse API mirror.
- **RB-PM08**: Preference `autoRefresh` MUST NOT activate automatic warehouse refresh on ELT page in current implementation (no consumer outside settings).
- **RB-PM09**: Timeline throughput, transformPct, dataQuality during simulation MAY use client-computed values; `recent_stages` from API reflect DB when available.
- **RB-PM10**: Endpoints `/stats/loads`, `/stats/synthetic/*`, `/analytics/warehouse` are accessible without server-side auth in current code (documented debt).
- **RB-PM11**: Analytical contract of `GET /stats/summary` remains owned by spec **007** when displayed on ELT page.
- **RB-PM12**: `GET /stats/loads` shared with explorer (**009**); 008 owns ELT page and synthetic registration context.

---

## Criterios de Aceptación Globales

1. **CA-001**: Engineer abre `/elt-pipeline` y ve KPIs iniciales (summary contextual, limits, last load, warehouse) trazados a CU-PM01.
2. **CA-002**: Warehouse status muestra layers, kpis, recent_stages cuando DB contiene ctl_pipeline_stages (CU-PM05).
3. **CA-003**: Historial cargas visible vía GET loads con campos ctl_carga_dataset (CU-PM04).
4. **CA-004**: Validación volumen bloquea run cuando excede limits o delta=0 (CU-PM02, M-13C).
5. **CA-005**: Ejecución UI completa con POST synthetic exitoso y registro ctl_carga_dataset (CU-PM03, M-13D).
6. **CA-006**: Timeline simulada y logs operativos durante run sin invocación elt_pipeline HTTP (CU-PM03, RB-PM01).
7. **CA-007**: Reset pipeline restaura estado idle (FR-PM15).
8. **CA-008**: Error synthetic deja estado failed y mensaje WARN (FR-PM17).
9. **CA-009**: Settings engineer tabs muestran contenido estático/local documentado (CU-PM07).
10. **CA-010**: Prefs pipeline persisten en localStorage (FR-PM19).
11. **CA-011**: Usuario no engineer bloqueado en `/elt-pipeline`; redirect `/etl-pipeline` funcional (M-13B).
12. **CA-012**: Operador puede ejecutar ELT medallion vía Docker/CLI documentado (CU-PM08, P7).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-PM01**: 95% cargas iniciales `/elt-pipeline` completan ≤ 4 s p95 con warehouse demo poblado (M-13A).
- **SC-PM02**: 100% intentos acceso `/elt-pipeline` por usuario no engineer bloqueados en frontend (M-13B).
- **SC-PM03**: 100% configuraciones synthetic inválidas en UI impiden POST (M-13C).
- **SC-PM04**: 100% POST synthetic exitosos en prueba integración registran fila ctl_carga_dataset (M-13D).
- **SC-PM05**: 0 invocaciones HTTP a elt_pipeline.py desde SPA en auditoría código (RB-PM01).
- **SC-PM06**: 100% filas matriz CU→FR→CA en spec 008 listas para TRACEABILITY-MASTER post-ratificación OT-08/OO-13.

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-PM01 | Usuario confunde simulación UI con ELT real | Alta | Alto | RB-PM01, US-PM03, CA-006, documentación explícita |
| R-PM02 | POST synthetic sin auth backend (P11) | Alta | Alto | RB-PM10, NFR-PM10; roadmap hardening fuera scope |
| R-PM03 | Overlap getSummary con spec 007 | Media | Medio | FR-PM21, RB-PM11 |
| R-PM04 | Settings autoRefresh implica refresh operativo | Media | Medio | RB-PM08, US-PM05 escenario 4 |
| R-PM05 | Tab warehouse settings parece live data | Media | Medio | RB-PM07, FR-PM18 |
| R-PM06 | Prefs pipeline no conectadas a ELT | Media | Bajo | RB-PM06 documentado |
| R-PM07 | Loads endpoint duplicado con 009 | Baja | Bajo | RB-PM12 delimitación |
| R-PM08 | Synthetic afecta KPIs 007 sin disclosure ELT | Media | Medio | P10 NFR-PM05; coordinación 007 |
| R-PM09 | Métricas timeline simuladas interpretadas como reales | Media | Medio | RB-PM09 |
| R-PM10 | Compose pipeline falla bloquea API | Baja | Alto | P7 NFR-PM06; CU-PM08 runbook |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| `001-user-identity-access` | Hard | Sesión, authGuard, engineerGuard, RB-015 |
| `006-account-self-service` | Soft | Visibilidad tabs engineer (FR-ST11); contenido 008 |
| `007-operational-analytics-dashboards` | Soft | Contrato `GET /stats/summary` contextual en ELT |
| Warehouse DuckDB poblado | Hard | dim_track, ctl_*, capas gold para monitoreo |
| `StatsService` métodos pipeline | Hard | getSyntheticLimits, generateSynthetic, getLastLoads, getWarehouseStatus, getSummary |
| `UiPreferencesService` | Soft | Prefs pipeline tab settings |
| `elt/pipelines/elt_pipeline.py` | Hard | ELT medallion fuera SPA |
| `docker-compose.yml` servicio pipeline | Hard | Orquestación P7 |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | P2 PKG-07, P6/P7 warehouse, P10 synthetic, P11 deuda auth, §12 trazabilidad |
| `SPEC-008-011-EVIDENCE-AUDIT.md` | Evidencia única autorizada para alcance 008 |
| `007-operational-analytics-dashboards/spec.md` | Out of Scope pipeline/synthetic |
| `TRACEABILITY-MASTER.md` | Integración filas 008 post-ratificación OT-08/OO-13 |

### Dependencias externas

| Dependencia | Descripción |
|-------------|-------------|
| Docker (opcional) | Ejecución servicio pipeline |
| DuckDB file | `data/warehouse/voxmetrik.duckdb` |

### Specs downstream (008 habilita / relaciona)

| Spec | Relación |
|------|----------|
| `009-data-explorer` | Comparte GET loads; explorer read-only |
| `007-operational-analytics-dashboards` | KPIs consumen warehouse post-synthetic |
| `011-health-operations` | Health independiente; compose orden pipeline→api |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§3.1 In Scope** | ELT UI, pipeline monitoring — evidenciado en código |
| **§4.3 Nivel Operativo** | ELT CLI/Docker, monitoreo cargas |
| **§5 P2 Package-by-Domain** | PKG-07 data-engineering |
| **§5 P6 Warehouse vs App** | Synthetic muta dim_track; monitoreo lee ctl_* |
| **§5 P7 ELT-before-API** | FR-PM24, NFR-PM06 compose |
| **§5 P10 Synthetic boundary** | NFR-PM05, RB-PM05 |
| **§5 P11 Security mutations** | RB-PM10 deuda auth synthetic/pipeline APIs |
| **§12 Trazabilidad** | Matriz OE→Impl en spec |
| **§14 Nomenclatura** | Branch `008-pipeline-monitoring` |

---

## Out of Scope

- Ejecución remota ELT medallion desde UI o API HTTP (ausente en código).
- WebSocket / polling server-push estado pipeline.
- Integración SPA `scripts/validate_warehouse.py` / `analyze_warehouse.py`.
- Alertas, SLA, notificaciones operativas, métricas APM.
- RBAC engineer en backend para endpoints pipeline/synthetic (no implementado).
- Cancelación/reintento job pipeline vía API.
- Auto-refresh operativo warehouse desde pref `autoRefresh` (sin consumidor).
- Settings warehouse tab como mirror live de `GET /analytics/warehouse`.
- Explorer tablas warehouse (**009**).
- Dashboards analíticos consumo BI (**007** salvo summary contextual).
- Health/root metadata (**011** / **006** tab api).
- PocketBase ingest UI.
- Endpoint `/api/info` (no existe).

---

## Assumptions

- Warehouse contiene filas en `dim_track` antes de synthetic útil (before > 0 para clonado).
- `ctl_carga_dataset` existe tras migraciones/ELT inicial.
- Rol engineer determinado por reglas **001** (`AuthService.hasEngineerAccess()`).
- Límites server-side `MAX_TARGET_TOTAL`, `MAX_CREATE_PER_RUN` alineados con `get_synthetic_limits()`.
- Entorno dev puede operar ELT page con API parcialmente degradada.
- `environment.apiUrl` apunta a API Voxmetriks operativa.
- Docker Compose disponible para operadores que ejecutan CU-PM08.
- Idiomas ES/EN suficientes para strings pipeline settings.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — evidencia `SPEC-008-011-EVIDENCE-AUDIT.md`  
**Next Step**: `/speckit-checklist` → `/speckit-plan` — Constitution Check P7, P10, P11; delimitación contracts con 006/007/009.
