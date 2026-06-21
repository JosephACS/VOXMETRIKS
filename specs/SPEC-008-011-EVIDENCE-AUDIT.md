# SPEC-008-011-EVIDENCE-AUDIT — Validación basada en código

**Versión:** 1.0.0  
**Fecha:** 2026-06-20  
**Rol:** Arquitecto principal — auditoría pre-spec  
**Alcance:** Evidencia en repositorio únicamente; **no** genera specs ni modifica documentación  
**Referencias:** Constitución v1.0.0 §3–§4, §5 P2/P6/P7/P10/P11; specs operativas **001–007** (delimitaciones Out of Scope)

**Metodología:** Inspección de `backend/app/**`, `frontend/src/app/**`, `app.routes.ts`, `elt/`, `scripts/`, `docker-compose.yml`. Toda afirmación cita artefacto verificable. **No se proponen funcionalidades nuevas.**

---

## 1. Resumen ejecutivo

| Spec futura | Nombre auditoría | ¿Existe en código? | % impl. actual | Estado |
|-------------|------------------|:------------------:|---------------:|--------|
| **008** | Pipeline Monitoring | **Sí** (parcial vs nombre) | **72 %** | **Lista para documentar** |
| **009** | Data Explorer | **Sí** | **91 %** | **Lista para documentar** |
| **010** | Catalog Steward | **Sí** (sin rol steward) | **78 %** | **Requiere auditoría adicional** |
| **011** | Health & Operations | **Sí** (operaciones limitadas) | **62 %** | **Requiere auditoría adicional** |

**Hallazgo transversal crítico:** Las cuatro áreas tienen **código implementado**, pero ninguna tiene spec propia. Spec **007** declara explícitamente Out of Scope para pipeline, explorer, steward y health (`007-operational-analytics-dashboards/spec.md` §Out of Scope). Spec **006** cubre parcialmente health (CU-ST05). Spec **003** excluye steward pero **comparte UI** con mutaciones CRUD en `/artists`, `/genres`, `/tracks`.

**Riesgo principal al documentar:** Inventar capacidades no presentes (ELT remoto vía API, rol steward, auto-refresh operativo, `/api/info`) o duplicar FR ya asignados a **003/006/007**.

---

## 2. Delimitación vs specs 001–007 (evidencia documental)

| Capacidad en código | Spec que la reclama hoy | Evidencia delimitación |
|---------------------|-------------------------|------------------------|
| `GET /stats/summary`, growth, top-tracks | **007** OO-12 | `007` FR-AN01–AN03; consumo BI |
| `GET /analytics/trending`, platform, engagement | **007** OO-12 | `007` FR-AN05–AN07 |
| `GET /analytics/warehouse`, `POST /stats/synthetic`, `GET /stats/loads` | **008** (sin spec) | `007` Out of Scope: pipeline/synthetic |
| `GET /analytics/explorer/*` | **009** (sin spec) | `007` Out of Scope: explorer |
| CRUD artists/genres/tracks UI + API | **003** lectura + **010** (sin spec) | `003` Out of Scope: steward CRUD |
| `GET /health`, tab api settings | **006** CU-ST05 + **011** (sin spec) | `006` FR-ST09–ST10; `007` Out of Scope health |
| `GET /` root metadata | **011** (sin spec) | Parcial; no en **006** |
| Engineer routes `/elt-pipeline`, `/explorer` | **001** FR-015 (FE) + **008/009** | `engineerGuard`; sin RBAC BE |

---

## 3. Spec 008 — Pipeline Monitoring

### 3.1 Funcionalidades realmente implementadas

| ID | Funcionalidad | Evidencia |
|----|---------------|-----------|
| E08-01 | Página ELT pipeline con KPIs warehouse | `EltPipelineComponent` — `elt-pipeline.component.ts` |
| E08-02 | Timeline Medallion simulado (extract→bronze→silver→gold→warehouse) | `timeline` signal + `runPipeline()` intervalos L376–415 |
| E08-03 | Log operativo en UI (INFO/WARN/SUCCESS) | `logs` signal + `addLog()` L484–487 |
| E08-04 | Generación sintética vía API | `POST /api/v1/stats/synthetic` → `stats.generateSynthetic()` L429; backend `stats.py` L57–69 |
| E08-05 | Consulta límites synthetic | `GET /api/v1/stats/synthetic/limits` — `stats.py` L52–54; UI L209–220 |
| E08-06 | Historial cargas (`ctl_carga_dataset`) | `GET /api/v1/stats/loads` — `stats.py` L90–95; `get_last_loads()` `stats_service.py` L118–137; UI ELT L237–240, Explorer L80–83 |
| E08-07 | Estado warehouse (capas, stages, KPIs) | `GET /api/v1/analytics/warehouse` — `analytics.py` L25–27; `get_warehouse_status()` `analytics_service.py` L37–90; UI ELT L242–267 |
| E08-08 | Validación volumen pre-ejecución (limits client-side) | `volumeValidation` computed L113–150 |
| E08-09 | Registro carga post-synthetic en `ctl_carga_dataset` | `generate_synthetic_tracks()` insert L349–360 `stats_service.py` |
| E08-10 | Lectura `ctl_pipeline_stages` en warehouse status | `analytics_service.py` L47–52 |
| E08-11 | Ruta protegida rol engineer (frontend) | `app.routes.ts` L122–127 `engineerGuard`; nav `dashboard-layout.component.ts` L131 |
| E08-12 | Pipeline ELT CLI/Docker (fuera SPA) | `docker-compose.yml` servicio `pipeline` L17–33; `elt/pipelines/elt_pipeline.py` |
| E08-13 | Tabs settings engineer warehouse/pipeline (estáticos) | `settings.component.ts` L112–118 engineer tabs; HTML `@case ('warehouse')`, `@case ('pipeline')` |

### 3.2 Funcionalidades parcialmente implementadas

| ID | Funcionalidad | Evidencia | Brecha |
|----|---------------|-----------|--------|
| P08-01 | **Ejecución pipeline ELT completa** | `runPipeline()` anima pasos L392–415; única llamada API real es `generateSynthetic` al final | No invoca `elt_pipeline.py` ni endpoint de orquestación |
| P08-02 | **Monitoreo stages reales** | `recent_stages` desde DB si existen L253–262 | Timeline mayormente simulado; métricas `throughput`, `dataQuality`, `transformPct` hardcoded/simulados L271–277, L454–455 |
| P08-03 | **Tab warehouse en Settings** | Lista `goldTables`, `aggregations` hardcoded L55–63 | No llama `getWarehouseStatus()`; path fijo L53 |
| P08-04 | **Tab pipeline en Settings** | Selects `defaultRecords`, `loadMode`, `autoRefresh` vía `UiPreferencesService` | Solo `localStorage` (`ui-preferences.service.ts` L132–147); **no** conecta a ELT ni API |
| P08-05 | **Auto-refresh warehouse** | Pref `autoRefresh` en settings HTML L571 | **Ningún** consumidor de `autoRefresh()` fuera de settings (grep `frontend/src`) |
| P08-06 | **Autorización engineer backend** | Endpoints synthetic/warehouse/loads sin `Depends(require_user_id)` ni rol | Contraste: `playlists.py` usa `require_user_id`; `stats.py`/`analytics.py` warehouse no |
| P08-07 | **Etiquetado P10 synthetic** | Tracks sintéticos con patrón `nombre_track NOT LIKE '%[syn-%'` L327–333 | Sin disclosure UI obligatorio en página ELT (sí en **005** recomendaciones) |

### 3.3 Funcionalidades ausentes (no inventar en spec)

- Endpoint HTTP para disparar `elt/pipelines/elt_pipeline.py`.
- WebSocket / polling server-push de estado pipeline.
- UI de monitoreo PocketBase ingest.
- Integración SPA de `scripts/validate_warehouse.py` / `analyze_warehouse.py`.
- Alertas, SLA, notificaciones operativas.
- RBAC engineer en backend para `/stats/synthetic`, `/analytics/warehouse`.
- Cancelación/reintento de job pipeline vía API.

### 3.4 Rutas frontend

| Ruta | Guard | Componente |
|------|-------|------------|
| `/elt-pipeline` | `authGuard` + `engineerGuard` | `EltPipelineComponent` |
| `/etl-pipeline` | redirect → `elt-pipeline` | — |
| `/settings` (tabs `warehouse`, `pipeline`) | `authGuard`; tabs solo engineer | `SettingsComponent` |

### 3.5 Endpoints backend

| Método | Ruta | Auth | Servicio |
|--------|------|------|----------|
| GET | `/api/v1/stats/loads` | No | `get_last_loads` |
| GET | `/api/v1/stats/synthetic/limits` | No | `get_synthetic_limits` |
| POST | `/api/v1/stats/synthetic` | No | `generate_synthetic_tracks` |
| GET | `/api/v1/analytics/warehouse` | No | `get_warehouse_status` |
| GET | `/api/v1/stats/summary` | No | usado en ELT (también **007**) |

**Nota:** `GET /stats/summary`, `catalog-growth` usados en ELT pertenecen funcionalmente a **007**; en spec **008** documentar solo uso contextual pipeline si se delimita.

### 3.6 Componentes Angular

- `packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` (+ `.html`, `.css`)
- `packages/administration/settings/settings.component.ts` (tabs warehouse/pipeline)
- `layouts/dashboard-layout/dashboard-layout.component.ts` (nav engineer)
- `shared/components/kpi-card/kpi-card.component.ts` (ELT KPIs)

### 3.7 Servicios

| Servicio | Métodos usados por 008 |
|----------|------------------------|
| `StatsService` | `getSummary`, `getLastLoads`, `getSyntheticLimits`, `generateSynthetic`, `getWarehouseStatus` |
| `UiPreferencesService` | `defaultRecords`, `loadMode`, `autoRefresh` (settings tab pipeline) |
| `AuthService` | `hasEngineerAccess()` vía guard |
| `IconRenderService` | iconografía ELT |

### 3.8 Casos de uso reales detectados (desde código, no ratificados)

| CU candidato | Evidencia flujo |
|--------------|-----------------|
| CU-PM01 | Engineer abre `/elt-pipeline` y ve KPIs + última carga | `ngOnInit` → `loadWarehouseKpis()` |
| CU-PM02 | Engineer configura volumen synthetic (multiplier/custom) | `selectMultiplier`, `onCustomTargetInput`, `applyIncrement` |
| CU-PM03 | Engineer ejecuta “pipeline” UI → genera synthetic | `runPipeline()` → `persistSynthetic()` |
| CU-PM04 | Engineer consulta historial cargas | `getLastLoads` en ELT y Explorer |
| CU-PM05 | Engineer consulta estado warehouse/capas | `getWarehouseStatus` |
| CU-PM06 | Engineer consulta límites antes de generar | `getSyntheticLimits` + `volumeValidation` |
| CU-PM07 | Engineer ve tabs warehouse/pipeline en settings | `engineerTabs` filter L112–125 |
| CU-PM08 | DevOps ejecuta ELT vía Docker CLI | `docker compose` servicio `pipeline` |

### 3.9 Historias de usuario candidatas

| HU candidata | Rol | Evidencia |
|--------------|-----|-----------|
| US-PM01 | Data Engineer | Ejecutar generación synthetic controlada desde ELT UI |
| US-PM02 | Data Engineer | Observar timeline y logs de ejecución |
| US-PM03 | Data Engineer | Consultar historial cargas warehouse |
| US-PM04 | Data Engineer | Ver estado capas Medallion y stages recientes |
| US-PM05 | DevOps | Ejecutar pipeline medallion fuera de SPA (CLI) |

### 3.10 FR candidatos (solo comportamiento observable)

| FR candidato | Comportamiento verificable |
|--------------|----------------------------|
| FR-PM01 | UI `/elt-pipeline` MUST cargar summary, limits, last load, warehouse status al init |
| FR-PM02 | UI MUST validar target synthetic contra limits antes de ejecutar |
| FR-PM03 | API MUST exponer POST `/stats/synthetic` con `target_total` o `multiplier` |
| FR-PM04 | API MUST exponer GET `/stats/loads` desde `ctl_carga_dataset` |
| FR-PM05 | API MUST exponer GET `/analytics/warehouse` con layers, kpis, recent_stages |
| FR-PM06 | API MUST exponer GET `/stats/synthetic/limits` |
| FR-PM07 | Ruta `/elt-pipeline` MUST requerir `engineerGuard` |
| FR-PM08 | Ejecución UI MUST registrar entrada en `ctl_carga_dataset` tras synthetic exitoso |
| FR-PM09 | Settings tabs warehouse/pipeline MUST ocultarse para no-engineer |

### 3.11 Riesgos de inventar requisitos

| Riesgo | Evidencia contraria |
|--------|---------------------|
| Documentar “ejecutar ELT medallion desde UI” | Solo animación + POST synthetic |
| Documentar auto-refresh operativo | Pref existe; sin listener en ELT/explorer |
| Documentar settings warehouse live | Arrays estáticos L55–63 |
| Duplicar FR-AN de **007** sin delimitación | Mismos endpoints summary/growth |
| Exigir RBAC backend no implementado | Sin `Depends` auth en stats synthetic |
| Nombrar “Monitoring” como observabilidad 24/7 | No hay polling/alerts |

### 3.12 % implementación y estado

**Cálculo:** 9 implementadas plenas + 7 parciales / 16 capacidades identificadas ≈ **72 %**  
**Estado:** **Lista para documentar** — acotar alcance a *monitoreo cargas + synthetic + warehouse status + UI engineer*, no orquestación ELT remota completa.

---

## 4. Spec 009 — Data Explorer

### 4.1 Funcionalidades realmente implementadas

| ID | Funcionalidad | Evidencia |
|----|---------------|-----------|
| E09-01 | Listado tablas warehouse con metadatos | `GET /analytics/explorer/tables` — `get_warehouse_tables()` L270–288 |
| E09-02 | Clasificación tabla (dimension/fact/aggregation/control/other) | `_table_kind()` L250–260; UI `kindCounts` L54–59 |
| E09-03 | Preview paginado filas | `GET /analytics/explorer/preview/{table_name}` — `get_table_preview()` L291–332 |
| E09-04 | Query SQL mostrada en UI | Campo `query` en respuesta preview L322; `sqlQuery` computed L42 |
| E09-05 | Filtro búsqueda tablas en UI | `searchFilter`, `filteredTables` L31–36, L100–102 |
| E09-06 | Paginación preview | `goPage`, `page`, `pageSize=8` L122–127 |
| E09-07 | Panel historial cargas en explorer | `getLastLoads(10)` L80–83 |
| E09-08 | Ruta engineer protegida | `app.routes.ts` L135–140 |
| E09-09 | Empty/error states | `hasError` signal L21; handlers L74–77, L96–97 |

### 4.2 Funcionalidades parcialmente implementadas

| ID | Funcionalidad | Evidencia | Brecha |
|----|---------------|-----------|--------|
| P09-01 | **Seguridad preview SQL** | Whitelist vía `_allowed_tables` L297–299 | Sin auth backend; cualquier cliente API puede consultar |
| P09-02 | **Export / download** | — | No existe |
| P09-03 | **Edición datos** | Preview read-only | Sin mutaciones (correcto para explorer) |

### 4.3 Funcionalidades ausentes

- UI para ejecutar SQL arbitrario (solo preview server-side).
- Linaje visual entre tablas (diagrama).
- Filtros columnares en preview.
- RBAC backend explorer endpoints.
- Integración con `ctl_auditoria` en UI.

### 4.4 Rutas frontend

| Ruta | Guard | Componente |
|------|-------|------------|
| `/explorer` | `authGuard` + `engineerGuard` | `ExplorerComponent` |

### 4.5 Endpoints backend

| Método | Ruta | Auth |
|--------|------|------|
| GET | `/api/v1/analytics/explorer/tables` | No |
| GET | `/api/v1/analytics/explorer/preview/{table_name}` | No |
| GET | `/api/v1/stats/loads` | No (panel cargas; overlap **008**) |

### 4.6 Componentes Angular

- `packages/data-engineering/explorer/explorer.component.ts` (+ `.html`, `.css`)
- `shared/components/kpi-card/kpi-card.component.ts`

### 4.7 Servicios

- `StatsService`: `getExplorerTables`, `getTablePreview`, `getLastLoads`

### 4.8 Casos de uso reales detectados

| CU candidato | Evidencia |
|--------------|-----------|
| CU-EX01 | Listar tablas warehouse | `ngOnInit` L64–77 |
| CU-EX02 | Filtrar tablas por nombre | `onFilterChange` L100–102 |
| CU-EX03 | Seleccionar tabla y ver preview | `selectTable` L86–89 |
| CU-EX04 | Paginar preview | `goPage` L122–127 |
| CU-EX05 | Ver conteos por tipo dim/fact/agg | `kindCounts` L54–59 |
| CU-EX06 | Ver historial cargas contextual | `loads` panel L80–83 |

### 4.9 Historias de usuario candidatas

| HU candidata | Rol |
|--------------|-----|
| US-EX01 | Data Engineer — navegar esquema warehouse |
| US-EX02 | Data Engineer — inspeccionar filas paginadas |
| US-EX03 | Analista — consultar historial cargas junto a tablas |

### 4.10 FR candidatos

| FR candidato | Comportamiento |
|--------------|----------------|
| FR-EX01 | API MUST listar tablas con name, kind, row_count, columns |
| FR-EX02 | API MUST preview paginado con page/limit y total |
| FR-EX03 | API MUST rechazar table_name no existente (404) |
| FR-EX04 | UI `/explorer` MUST filtrar tablas client-side |
| FR-EX05 | UI MUST paginar preview |
| FR-EX06 | Ruta MUST requerir engineerGuard |
| FR-EX07 | UI MUST mostrar SQL query retornada por API |

### 4.11 Riesgos de inventar requisitos

| Riesgo | Evidencia |
|--------|-----------|
| SQL editor libre | No existe; solo preview endpoint |
| CRUD desde explorer | No hay mutaciones |
| Duplicar loads en **008** | Mismo endpoint; delimitar en spec |

### 4.12 % implementación y estado

**Cálculo:** 9/10 capacidades core ≈ **91 %**  
**Estado:** **Lista para documentar** — spec acotada a inspección read-only warehouse.

---

## 5. Spec 010 — Catalog Steward

### 5.1 Funcionalidades realmente implementadas

| ID | Funcionalidad | Evidencia |
|----|---------------|-----------|
| E10-01 | POST/PUT/DELETE artistas API | `artists.py` L34, L63, L77 |
| E10-02 | POST/PUT/DELETE géneros API | `genres.py` L34, L63, L77 |
| E10-03 | POST/PUT/DELETE tracks API | `tracks.py` L50, L91, L112 |
| E10-04 | UI crear/editar/eliminar artista | `artists.component.ts` modales L141–174 |
| E10-05 | UI crear/editar/eliminar género | `genres.component.ts` (grep create/update/delete) |
| E10-06 | UI crear/editar/eliminar track | `tracks.component.ts` L106–134 |
| E10-07 | Servicios FE CRUD | `ArtistsService`, `GenresService`, `TracksService` métodos post/put/delete |
| E10-08 | Validación nombre vacío en UI | p.ej. `artists.component.ts` L143 |
| E10-09 | Manejo errores API en modales | `error: (e) => formError.set(e?.error?.detail ...)` |

### 5.2 Funcionalidades parcialmente implementadas

| ID | Funcionalidad | Evidencia | Brecha |
|----|---------------|-----------|--------|
| P10-01 | **Rol steward** | CRUD en páginas catálogo **003** `/artists`, `/genres`, `/tracks` | Cualquier usuario autenticado; no hay `stewardGuard` |
| P10-02 | **Auth backend mutaciones** | `Depends(get_write_conn)` solo | Sin `require_user_id` (contraste `playlists.py` L13) |
| P10-03 | **Auditoría mutaciones** | `ctl_auditoria` en ELT | No invocado en routes streaming CRUD |
| P10-04 | **Separación spec 003 vs 010** | Misma UI lista + modales steward | `003` Out of Scope steward L465; código mezclado |

### 5.3 Funcionalidades ausentes

- Rol/permiso steward dedicado (Constitución P11 target).
- Pantalla steward separada de consumo catálogo.
- Log auditoría visible en UI.
- Validaciones de negocio avanzadas (integridad referencial documentada en spec).
- Confirmación dual para DELETE en API (solo UI modal).

### 5.4 Rutas frontend

| Ruta | Guard | CRUD UI |
|------|-------|---------|
| `/artists` | `authGuard` | create/edit/delete modales |
| `/genres` | `authGuard` | create/edit/delete modales |
| `/tracks` | `authGuard` | create/edit/delete modales |

**Nota:** Rutas pertenecen al dominio **003**; spec **010** debe delimitar steward vs consumo.

### 5.5 Endpoints backend

| Método | Ruta | Auth |
|--------|------|------|
| POST | `/api/v1/artists` | No |
| PUT | `/api/v1/artists/{id}` | No |
| DELETE | `/api/v1/artists/{id}` | No |
| POST | `/api/v1/genres` | No |
| PUT | `/api/v1/genres/{id}` | No |
| DELETE | `/api/v1/genres/{id}` | No |
| POST | `/api/v1/tracks` | No |
| PUT | `/api/v1/tracks/{id}` | No |
| DELETE | `/api/v1/tracks/{id}` | No |

### 5.6 Componentes Angular

- `packages/streaming/artists/artists.component.ts`
- `packages/streaming/genres/genres.component.ts`
- `packages/streaming/tracks/tracks.component.ts`

### 5.7 Servicios

- `ArtistsService` — `createArtist`, `updateArtist`, `deleteArtist`
- `GenresService` — `createGenre`, `updateGenre`, `deleteGenre`
- `TracksService` — `createTrack`, `updateTrack`, `deleteTrack`

### 5.8 Casos de uso reales detectados

| CU candidato | Evidencia |
|--------------|-----------|
| CU-STW01 | Crear artista desde modal | `saveCreate` artists L141–149 |
| CU-STW02 | Editar artista | `saveEdit` L152–163 |
| CU-STW03 | Eliminar artista | `confirmDelete` L165–174 |
| CU-STW04 | CRUD género | `genres.component.ts` |
| CU-STW05 | CRUD track | `tracks.component.ts` L106–134 |

### 5.9 Historias de usuario candidatas

| HU candidata | Observación |
|--------------|-------------|
| US-STW01 | Usuario autenticado administra artistas — **no** rol steward separado hoy |
| US-STW02 | Usuario autenticado administra géneros |
| US-STW03 | Usuario autenticado administra tracks |

### 5.10 FR candidatos

| FR candidato | Evidencia |
|--------------|-----------|
| FR-STW01 | API POST/PUT/DELETE artists MUST mutar `dim_artista` vía write conn |
| FR-STW02 | API POST/PUT/DELETE genres MUST mutar dim género |
| FR-STW03 | API POST/PUT/DELETE tracks MUST mutar dim_track |
| FR-STW04 | UI artists MUST exponer modales create/edit/delete |
| FR-STW05 | UI genres MUST exponer modales create/edit/delete |
| FR-STW06 | UI tracks MUST exponer modales create/edit/delete |
| FR-STW07 | UI MUST mostrar error API en modal |

### 5.11 Riesgos de inventar requisitos

| Riesgo | Evidencia |
|--------|-----------|
| “Solo API, sin UI” | **Falso** — modales en 3 componentes |
| “Solo steward role” | **Falso** — cualquier auth user |
| Duplicar CU-C* de **003** | Misma pantalla; requiere auditoría delimitación |
| Exigir auditoría ctl | No implementada en routes |

### 5.12 % implementación y estado

**Cálculo:** CRUD end-to-end ~88 %; gobernanza steward ~30 % → **78 %** ponderado  
**Estado:** **Requiere auditoría adicional** — solapamiento crítico con **003** y ausencia rol/auth antes de redactar spec.

---

## 6. Spec 011 — Health & Operations

### 6.1 Funcionalidades realmente implementadas

| ID | Funcionalidad | Evidencia |
|----|---------------|-----------|
| E11-01 | Health check API | `GET /health` — `main.py` L151–179 |
| E11-02 | Root metadata API | `GET /` — `main.py` L141–148 (`app`, `version`, `docs`, `health`) |
| E11-03 | Modelo HealthResponse | `models.py` L218–222: status, database, tables, version |
| E11-04 | UI health en Settings tab `api` | `refreshHealth()` L202–211; HTML L383–397 |
| E11-05 | Estados degraded/error/ok en UI | `healthStatusClass`, `healthStatusText` L216–229 |
| E11-06 | StatsService.getHealth | `stats.service.ts` L88–91 → `/health` |
| E11-07 | Docker compose dependencia pipeline→api | `docker-compose.yml` — api espera pipeline |

### 6.2 Funcionalidades parcialmente implementadas

| ID | Funcionalidad | Evidencia | Brecha |
|----|---------------|-----------|--------|
| P11-01 | **Cobertura spec 006** | CU-ST05, FR-ST09–ST10 | Root `/` no en **006** |
| P11-02 | **Operaciones ampliadas** | Nombre “Health & Operations” | Sin ruta `/operations`; sin runbook SPA |
| P11-03 | **Tests health** | `test_api.py` L34–39 | Espera schema distinto en root L26–32 (`status: running` vs `{app, version}`) |
| P11-04 | **Endpoint `/api/info`** | Test L41–47 | **No existe** en `main.py` |
| P11-05 | **Scripts operativos** | `scripts/validate_warehouse.py` | CLI only; no UI |

### 6.3 Funcionalidades ausentes

- Pantalla dedicada operaciones/monitoreo sistema.
- Exposición UI de `GET /` root metadata.
- Métricas runtime (CPU, memoria, latencia p95).
- Estado servicio PocketBase en SPA.
- Alerting / incidentes.
- Auto-refresh health periódico (solo botón manual refresh).

### 6.4 Rutas frontend

| Ruta | Sección | Evidencia |
|------|---------|-----------|
| `/settings` | Tab `api` (health) | `settings.component.ts` L136, L202–211 |
| — | No hay ruta `/operations` | — |

### 6.5 Endpoints backend

| Método | Ruta | Respuesta clave |
|--------|------|-----------------|
| GET | `/health` | status, database, tables[], version |
| GET | `/` | app, version, docs, health |

### 6.6 Componentes Angular

- `packages/administration/settings/settings.component.ts` (+ HTML tab api)

### 6.7 Servicios

- `StatsService.getHealth()`
- (Transversal) `UiPreferencesService` — no aplica directamente a health

### 6.8 Casos de uso reales detectados

| CU candidato | Evidencia |
|--------------|-----------|
| CU-HO01 | Usuario consulta health en settings | `selectTab('api')` → `refreshHealth` |
| CU-HO02 | Usuario refresca health manualmente | Botón L395–397 |
| CU-HO03 | Integrador consulta root API | Endpoint `/` (sin UI) |
| CU-HO04 | Sistema reporta degraded si DB missing | `main.py` L154–160 |

### 6.9 Historias de usuario candidatas

| HU candidata | Rol |
|--------------|-----|
| US-HO01 | Usuario autenticado — ver health backend en settings |
| US-HO02 | Operador — consultar metadata API (integración externa, sin UI) |

### 6.10 FR candidatos

| FR candidato | Evidencia |
|--------------|-----------|
| FR-HO01 | API MUST responder GET `/health` con status ok/degraded/error |
| FR-HO02 | API MUST incluir database path, tables list, version en health |
| FR-HO03 | API MUST responder GET `/` con app name y version |
| FR-HO04 | UI settings tab api MUST fetch y mostrar health |
| FR-HO05 | UI MUST manejar error conexión sin stack trace (align **006** RB-ST06) |

### 6.11 Riesgos de inventar requisitos

| Riesgo | Evidencia |
|--------|-----------|
| Documentar `/api/info` | Test legacy; endpoint ausente |
| “Operations suite” completa | Solo health + compose + scripts CLI |
| Duplicar **006** CU-ST05 sin enmienda | Overlap documental |
| Prometheus/metrics | No en código |

### 6.12 % implementación y estado

**Cálculo:** Health path completo ~85 %; “Operations” más allá health ~25 % → **62 %**  
**Estado:** **Requiere auditoría adicional** — decidir si **011** es extensión de **006** o spec mínima root+health; nombre “Operations” sobredimensiona código actual.

---

## 7. Tabla resumen — Spec | % Implementación | Estado

| Spec | Nombre | % Implementación actual | Estado | Nota evidencia |
|------|--------|------------------------:|--------|----------------|
| **008** | Pipeline Monitoring | **72 %** | **Lista para documentar** | Synthetic + loads + warehouse UI; ELT real solo CLI/Docker |
| **009** | Data Explorer | **91 %** | **Lista para documentar** | Explorer UI+API completos; read-only |
| **010** | Catalog Steward | **78 %** | **Requiere auditoría adicional** | CRUD FE+BE; overlap **003**; sin rol/auth |
| **011** | Health & Operations | **62 %** | **Requiere auditoría adicional** | Health sólido; “operations” limitado; overlap **006** |

**Ninguna spec 008–011 cae en estado “No existe en código”.**

---

## 8. Matriz de solapamiento StatsService (evidencia técnica)

Métodos en `frontend/src/app/packages/analytics/services/stats.service.ts` por spec futura:

| Método | Endpoint | Spec propietaria actual/futura |
|--------|----------|-------------------------------|
| `getSummary` | `/stats/summary` | **007** |
| `getCatalogGrowth` | `/stats/catalog-growth` | **007** |
| `getTopTracks` | `/stats/top-tracks` | **007** |
| `getEnergyDistribution` | `/stats/energy-distribution` | **007** |
| `getTrendingAnalytics` | `/analytics/trending` | **007** |
| `getPlatformAnalytics` | `/analytics/platform` | **007** |
| `getEngagementAnalytics` | `/analytics/engagement` | **007** |
| `getRecommendations` | `/analytics/recommendations` | **005** |
| `getHistoryHub` | `/analytics/history` | **005** |
| `getLastLoads` | `/stats/loads` | **008** (+ **009** panel) |
| `getSyntheticLimits` | `/stats/synthetic/limits` | **008** |
| `generateSynthetic` | POST `/stats/synthetic` | **008** |
| `getWarehouseStatus` | `/analytics/warehouse` | **008** |
| `getExplorerTables` | `/analytics/explorer/tables` | **009** |
| `getTablePreview` | `/analytics/explorer/preview/{table}` | **009** |
| `getHealth` | `/health` | **006** / **011** |
| `getGenreStats` | `/genres/stats` | **003** / **007** |

**Implicación:** Spec **008/009/011** deben delimitar métodos StatsService vs **007** al redactarse.

---

## 9. Constitución — evidencia relevante (sin interpretar más allá del texto)

| Sección / Principio | Relación con 008–011 |
|---------------------|----------------------|
| §3.1 In Scope | Analytics, ELT UI, explorer — **código presente** |
| §4.3 Nivel operativo | Pipeline CLI, health — **código presente** |
| P2 Package-by-domain | `data-engineering/` FE; analytics BE — **alineado** |
| P6 Warehouse vs app | Synthetic muta `dim_track`; CRUD muta dims — **warehouse writes** |
| P7 ELT-before-API | Compose pipeline before api — **implementado** |
| P10 Synthetic boundary | Generación existe; disclosure parcial — **documentar con cuidado en 008** |
| P11 Security mutations | CRUD/synthetic **sin auth** — **brecha vs target** |

---

## 10. Recomendaciones pre-redacción (no specs)

1. **008 primero** — mayor evidencia, delimitar explícitamente que “run pipeline UI” = synthetic + simulación visual, no `elt_pipeline.py`.
2. **009 inmediatamente después** — spec más acotada; riesgo bajo si se mantiene read-only.
3. **010 solo tras auditoría delimitación 003** — decidir si modales CRUD son steward (**010**) o extensión no gobernada de **003**.
4. **011 como extensión mínima** — health + root; evitar “Operations” amplias sin código; resolver overlap **006** CU-ST05.
5. **No documentar** `/api/info`, auto-refresh operativo, ELT HTTP trigger, rol steward, ni métricas APM — **ausentes en código**.
6. Actualizar `OPERATIVE-GAP-ANALYSIS.md` en fase posterior (fuera de este audit) — aún lista analytics sin spec **007**.

---

## 11. Conclusión

Las cuatro specs futuras tienen **base de código verificable**. La evidencia **no** justifica specs “greenfield”: son principalmente **formalización SDD** de comportamiento ya desplegado, con delimitaciones estrictas contra **003/006/007** y con **008/011** requiriendo acotación nominal (Monitoring ≠ orquestación ELT remota; Operations ≠ plataforma observability completa).

**008 y 009** están **listas para documentar** con alcance derivado del código.  
**010 y 011** requieren **auditoría adicional** de delimitación documental antes de `/speckit-specify`.

---

**Elaborado por:** Auditoría evidencia código — arquitectura Voxmetriks  
**Artefacto:** `specs/SPEC-008-011-EVIDENCE-AUDIT.md`  
**Sin modificaciones** al repositorio salvo este informe
