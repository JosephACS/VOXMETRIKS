# OPERATIVE-GAP-ANALYSIS — Funcionalidad sin Spec Operativa

> **⚠️ DOCUMENTO ARCHIVADO (solo referencia histórica)**  
> **Estado:** Superseded by TRACEABILITY-MASTER v2.0.0 + specs **008–011** (2026-06-19).  
> Las brechas G-D01…G-D04 descritas abajo están **cerradas documentalmente**.  
> Para verificación actual: [`DELIVERY-VERIFICATION-CHECKLIST.md`](DELIVERY-VERIFICATION-CHECKLIST.md) · [`TRACEABILITY-COVERAGE-REPORT.md`](TRACEABILITY-COVERAGE-REPORT.md) v2.0.0.

| Brecha histórica | Spec creada | Estado |
|------------------|-------------|--------|
| Analítica dashboards | **007** | ✅ Cerrada (pre-archivo) |
| Pipeline ELT / synthetic | **008** | ✅ Cerrada |
| Warehouse explorer | **009** | ✅ Cerrada |
| CRUD steward | **010** | ✅ Cerrada (FR-CS15 Parcial) |
| Health / root API | **011** | ✅ Cerrada |

**Versión:** 1.0.0 (archivada)  
**Fecha original:** 2026-06-20  
**Alcance original:** Código vs specs `001`–`006`  
**Referencias:** Constitución v1.0.0 §3–§4, §12; `TRACEABILITY-MASTER.md`; `DOCUMENT-COVERAGE-REPORT.md` §7  
**Metodología:** Inventario de rutas Angular, endpoints FastAPI, servicios y módulos ELT; contraste con cadena OE→OT→OO de la matriz maestra (OO-01…OO-11, OO-15).

---

## 1. Resumen ejecutivo (histórico — pre-spec 007–011)

Las specs **001–006** cubren la **operativa de consumo musical personalizado** (identidad, biblioteca, catálogo-lectura, reproductor, recomendaciones/historial, autogestión). El código implementa **~40% adicional de superficie operativa** sin spec dedicada, concentrada en:

1. **Analítica operativa de plataforma** (dashboards, trending, engagement, comparativas).
2. **Ingeniería de datos en UI** (pipeline ELT, generación sintética, estado warehouse).
3. **Exploración del warehouse** (metadatos, preview SQL, historial de cargas).
4. **APIs de soporte analítico** usadas transversalmente (stats summary, catalog growth, loads).
5. **CRUD steward de catálogo** (explícitamente fuera de actor principal en spec 003, pero implementado en backend).

La Constitución §3.1 incluye estas capacidades en *In Scope*; `DOCUMENT-COVERAGE-REPORT.md` §7 las declara **fuera de mandato 001–006**. Este informe cuantifica la brecha operativa real.

---

## 2. Inventario de módulos operativos existentes en código

### 2.1 Frontend (`frontend/src/app`)

| Módulo / paquete | Componentes principales | Rutas | Spec actual |
|------------------|-------------------------|-------|-------------|
| `pages/login` | LoginComponent | `/login` | **001** |
| `packages/users` | UsersComponent | `/users` | **006** (OO-11) |
| `packages/administration/settings` | SettingsComponent | `/settings` | **006** (OO-10) |
| `packages/streaming/*` | home, artists, tracks, track-detail, genres, search, playlists, liked, audio-features | `/dashboard`, `/artists`, `/tracks`, `/search`, `/playlists`, `/liked`, `/genres`, `/audio-features` | **003**, **004** (home), **002** |
| `packages/history` | HistoryComponent | `/history` | **005** (OO-09) |
| `packages/recommendations` | RecommendationsComponent | `/recommendations` | **005** (OO-08) |
| `core` + `layouts` | auth, guards, player, dashboard-layout | (transversal) | **001**, **004** |
| `packages/analytics/dashboard` | DashboardComponent | `/dashboard/analytics` | **Sin spec** |
| `packages/analytics/trending` | TrendingComponent | `/trending` | **Sin spec** |
| `packages/analytics/analytics` | AnalyticsComponent | `/analytics` | **Sin spec** |
| `packages/analytics/comparatives` | ComparativesComponent | `/comparativas` | **Sin spec** |
| `packages/data-engineering/elt-pipeline` | EltPipelineComponent | `/elt-pipeline` | **Sin spec** (parcial 001/006 engineer) |
| `packages/data-engineering/explorer` | ExplorerComponent | `/explorer` | **Sin spec** |
| `shared/services` | MusicPlayerService, StatsService, etc. | — | Mixto |

**Servicios Angular con métodos sin trazabilidad spec dedicada** (`StatsService`):

| Método | Endpoint(s) | Consumidores sin spec analítica |
|--------|-------------|--------------------------------|
| `getSummary` | `GET /api/v1/stats/summary` | Home, Dashboard, ELT, Login |
| `getCatalogGrowth` | `GET /api/v1/stats/catalog-growth` | Home, Dashboard |
| `getTopTracks` | `GET /api/v1/stats/top-tracks` | Home, Dashboard |
| `getEnergyDistribution` | `GET /api/v1/stats/energy-distribution` | Analytics, Audio-features (parcial 003) |
| `getLastLoads` | `GET /api/v1/stats/loads` | ELT, Explorer |
| `generateSynthetic` | `POST /api/v1/stats/synthetic` | ELT |
| `getSyntheticLimits` | `GET /api/v1/stats/synthetic/limits` | ELT |
| `getWarehouseStatus` | `GET /api/v1/analytics/warehouse` | ELT |
| `getTrendingAnalytics` | `GET /api/v1/analytics/trending` | Trending, Users (parcial) |
| `getPlatformAnalytics` | `GET /api/v1/analytics/platform` | Users (parcial) |
| `getEngagementAnalytics` | `GET /api/v1/analytics/engagement` | Analytics |
| `getExplorerTables` | `GET /api/v1/analytics/explorer/tables` | Explorer |
| `getTablePreview` | `GET /api/v1/analytics/explorer/preview/{table}` | Explorer |
| `getHealth` | `GET /health` | Settings (**006** ST05) |
| `getRecommendations` | `GET /api/v1/analytics/recommendations` | Recommendations (**005**) |
| `getHistoryHub` | `GET /api/v1/analytics/history` | History (**005**) |

### 2.2 Backend (`backend/app`)

| Paquete | Router prefix | Endpoints | Spec actual |
|---------|---------------|-----------|-------------|
| `users` | `/api/v1/users` | login, register, me, preferences | **001**, **006** |
| `streaming` playlists/favorites | `/api/v1/playlists`, `/favorites` | CRUD + junction | **002** |
| `streaming` artists/genres/tracks | `/api/v1/artists`, `/genres`, `/tracks` | lectura + **CRUD steward** | Lectura **003**; CRUD **sin spec** |
| `analytics` stats | `/api/v1/stats` | summary, growth, top-tracks, loads, synthetic, energia | **Sin spec** (uso transversal) |
| `analytics` analytics | `/api/v1/analytics` | warehouse, trending, platform, engagement, explorer, history, recommendations | Parcial **005**; resto **sin spec** |
| `main` | `/`, `/health` | root metadata, health | Parcial **006** ST05 |

### 2.3 ELT / operaciones fuera de API (`elt/`, `scripts/`)

| Módulo | Función | UI/API | Spec |
|--------|---------|--------|------|
| `elt/pipelines/elt_pipeline.py` | Pipeline Medallion completo | Docker `pipeline` service; no UI directa salvo ELT page synthetic | **Sin spec** |
| `elt/transform/enterprise_analytics.py` | Capa synthetic behavioral | Invocado por pipeline y POST synthetic | **Sin spec** (P10 boundary parcial en **005** FR-RC05) |
| `elt/extract/*`, `elt/load/*` | Bootstrap, download, drop | Scripts/CLI | **Sin spec** |
| `scripts/validate_warehouse.py`, `analyze_warehouse.py` | Validación offline | CLI | **Sin spec** |
| `pocketbase/` | Ingesta datasets | Docker; sin ruta SPA | **Sin spec** |

### 2.4 Objetivos operativos (OO) en TRACEABILITY-MASTER

| OO | Spec | Descripción (desde specs) |
|----|------|---------------------------|
| OO-01 | 001 | Identidad y acceso |
| OO-02 | 002 | Playlists |
| OO-03 | 002 | Favoritos |
| OO-04 | 003 | Explorar catálogo |
| OO-05 | 003 | Búsqueda |
| OO-06 | 004 | Reproductor |
| OO-07 | 004 | Home hub |
| OO-08 | 005 | Recomendaciones |
| OO-09 | 005 | Historial unificado |
| OO-10 | 006 | Preferencias / settings |
| OO-11 | 006 | Perfil UI |
| OO-15 | 003 | Audio features |

**OO no definidos en matriz maestra pero presentes en código:** requieren nuevos OT/OO (propuesta §8).

---

## 3. Funcionalidades implementadas sin spec operativa propia

### 3.1 Dominio A — Analítica operativa de plataforma

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-A01** | Panel analítico KPI warehouse | `DashboardComponent`, `/dashboard/analytics` | Usa summary, growth, top-tracks |
| **GAP-A02** | Tendencias y streams diarios | `TrendingComponent`, `/trending` | `GET /analytics/trending` |
| **GAP-A03** | Análisis engagement + energía + géneros | `AnalyticsComponent`, `/analytics` | engagement + energy-distribution |
| **GAP-A04** | Comparativas inter-género (radar) | `ComparativesComponent`, `/comparativas` | Solo `genres/stats`; UI analítica pura |
| **GAP-A05** | KPI rail analítico en Home | `home.component` → stats summary/growth | Mezcla **004** home con analítica |
| **GAP-A06** | Stats de plataforma en perfil | `users.component` → platform/trending | Mezcla **006** perfil con analítica |
| **GAP-A07** | APIs platform + engagement | Backend `analytics.py` | Sin actor CU en 001–006 |

### 3.2 Dominio B — Ingeniería de datos (UI + API)

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-B01** | UI Pipeline ELT + timeline simulado | `EltPipelineComponent`, `/elt-pipeline` | Engineer guard; no spec CU |
| **GAP-B02** | Generación sintética vía API | `POST /stats/synthetic`, ELT UI | Constitución P10; solo disclaimer en **005** |
| **GAP-B03** | Límites generación sintética | `GET /stats/synthetic/limits` | ELT UI |
| **GAP-B04** | Estado warehouse (capas, stages) | `GET /analytics/warehouse` | ELT + settings tab engineer |
| **GAP-B05** | Historial cargas pipeline | `GET /stats/loads` | Explorer + ELT |
| **GAP-B06** | Pipeline CLI/Docker | `elt/pipelines/elt_pipeline.py`, compose | Operativo §4.3 Constitución; sin spec |

### 3.3 Dominio C — Exploración warehouse

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-C01** | Listado tablas warehouse | `GET /analytics/explorer/tables` | Explorer UI |
| **GAP-C02** | Preview paginado + query | `GET /analytics/explorer/preview/{table}` | Explorer UI |
| **GAP-C03** | Clasificación dim/fact/agg en UI | `explorer.component` kindCounts | Metadatos operativos |

### 3.4 Dominio D — Stats transversales (sin pantalla única)

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-D01** | Resumen global catálogo | `GET /stats/summary` | Home, Dashboard, Login, ELT |
| **GAP-D02** | Crecimiento catálogo temporal | `GET /stats/catalog-growth` | Home, Dashboard |
| **GAP-D03** | Top tracks por popularidad (stats) | `GET /stats/top-tracks` | Home, Dashboard (distinto de trending) |
| **GAP-D04** | Distribución energía (stats alias) | `GET /stats/energia`, `/energy-distribution` | Analytics; overlap **003** OO-15 |

### 3.5 Dominio E — Stewardship catálogo (backend)

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-E01** | CRUD artistas sin auth | POST/PUT/DELETE `/artists` | Spec **003** Out of Scope steward |
| **GAP-E02** | CRUD géneros sin auth | POST/PUT/DELETE `/genres` | Idem |
| **GAP-E03** | CRUD tracks sin auth | POST/PUT/DELETE `/tracks` | Idem |

### 3.6 Dominio F — Infraestructura / plataforma

| ID | Funcionalidad | Evidencia | Notas |
|----|---------------|-----------|-------|
| **GAP-F01** | Root API metadata | `GET /` | No CU |
| **GAP-F02** | Health check sistema | `GET /health` | Parcial **006** CU-ST05; no cubre `/` |
| **GAP-F03** | Login showcase stats | `login.component` → getSummary | Fuera **001** |

### 3.7 Cobertura parcial (spec existe pero código excede alcance)

| Área | Spec | Brecha |
|------|------|--------|
| Home `/dashboard` | **004** OO-07 | Incorpora KPIs warehouse (GAP-A05) no descritos como analítica en **004** |
| Settings engineer tabs | **006** ST06 | Warehouse/pipeline tabs sin FR de contenido warehouse (GAP-B04) |
| Recomendaciones | **005** | Backend usa agregados enterprise; P10 solo UI disclaimer |
| Historial hub | **005** | Mezcla `fact_searches` warehouse + local; reglas merge parciales |
| Engineer role | **001** FR-015 | Guard frontend; APIs synthetic/explorer **sin auth backend** |

---

## 4. Rutas frontend afectadas (sin spec dedicada)

| Ruta | Componente | GAP IDs |
|------|------------|---------|
| `/dashboard/analytics` | DashboardComponent | A01, D01–D03 |
| `/trending` | TrendingComponent | A02, A07 |
| `/analytics` | AnalyticsComponent | A03, A07, D04 |
| `/comparatives` | ComparativesComponent | A04 |
| `/elt-pipeline` | EltPipelineComponent | B01–B06 |
| `/etl-pipeline` | redirect → elt-pipeline | B01 |
| `/explorer` | ExplorerComponent | C01–C03, B05 |
| `/dashboard` (rail analítico) | HomeComponent | A05, D01–D02 |
| `/users` (widgets analytics) | UsersComponent | A06, A07 |
| `/login` (stats preview) | LoginComponent | F03, D01 |
| `/settings` (tabs warehouse/pipeline) | SettingsComponent | B04, B06 (parcial **006**) |

**Rutas cubiertas por 001–006:** `/login`, `/users`, `/settings` (core), `/playlists`, `/liked`, `/history`, `/recommendations`, `/tracks`, `/tracks/:id`, `/artists`, `/genres`, `/search`, `/audio-features`, reproductor global.

---

## 5. Endpoints backend afectados (sin spec dedicada)

### 5.1 `/api/v1/stats/*` — Dominio D (+ B2–B3)

| Método | Ruta | GAP |
|--------|------|-----|
| GET | `/stats/summary` | D01 |
| GET | `/stats/catalog-growth` | D02 |
| GET | `/stats/top-tracks` | D03 |
| GET | `/stats/loads` | B05, C03 |
| GET | `/stats/synthetic/limits` | B03 |
| POST | `/stats/synthetic` | B02 |
| GET | `/stats/energia` | D04 |
| GET | `/stats/energy-distribution` | D04 |

### 5.2 `/api/v1/analytics/*` — Dominios A, B, C (excepto history/recommendations)

| Método | Ruta | GAP |
|--------|------|-----|
| GET | `/analytics/warehouse` | B04 |
| GET | `/analytics/trending` | A02 |
| GET | `/analytics/platform` | A07 |
| GET | `/analytics/engagement` | A03 |
| GET | `/analytics/explorer/tables` | C01 |
| GET | `/analytics/explorer/preview/{table_name}` | C02 |

### 5.3 `/api/v1/{artists|genres|tracks}` — Dominio E

| Método | Recurso | GAP |
|--------|---------|-----|
| POST, PUT, DELETE | artists, genres, tracks | E01–E03 |

### 5.4 Raíz

| Método | Ruta | GAP |
|--------|------|-----|
| GET | `/` | F01 |
| GET | `/health` | F02 (parcial **006**) |

**Endpoints cubiertos por 001–006:** users auth/profile; playlists; favorites; GET catalog/search/features; analytics/history; analytics/recommendations.

---

## 6. Casos de uso candidatos (propuesta, no ratificados)

### Spec candidata **007 — Operational Analytics & Dashboards**

| CU candidato | Descripción | Rutas / endpoints |
|--------------|-------------|-------------------|
| CU-AN01 | Ver panel analítico KPI catálogo | `/dashboard/analytics`, `/stats/summary` |
| CU-AN02 | Ver evolución crecimiento catálogo | `/stats/catalog-growth` |
| CU-AN03 | Ver trending tracks y streams | `/trending`, `/analytics/trending` |
| CU-AN04 | Ver métricas engagement plataforma | `/analytics`, `/analytics/engagement` |
| CU-AN05 | Comparar géneros (radar/insights) | `/comparatives` |
| CU-AN06 | Ver uso plataforma por dispositivo | `/analytics/platform`, perfil users |
| CU-AN07 | Consumir top tracks stats (no trending) | `/stats/top-tracks` |

### Spec candidata **008 — Data Pipeline & Synthetic Operations**

| CU candidato | Descripción | Rutas / endpoints |
|--------------|-------------|-------------------|
| CU-EL01 | Ver estado warehouse y capas | `/analytics/warehouse`, settings warehouse tab |
| CU-EL02 | Ver historial cargas ELT | `/stats/loads` |
| CU-EL03 | Ejecutar generación sintética controlada | `POST /stats/synthetic`, ELT UI |
| CU-EL04 | Consultar límites synthetic | `/stats/synthetic/limits` |
| CU-EL05 | Operar UI pipeline ELT (engineer) | `/elt-pipeline` |
| CU-EL06 | Ejecutar pipeline medallion (CLI/Docker) | `elt_pipeline.py`, compose |

### Spec candidata **009 — Warehouse Explorer & Data Inspection**

| CU candidato | Descripción | Rutas / endpoints |
|--------------|-------------|-------------------|
| CU-EX01 | Listar tablas warehouse con metadatos | `/analytics/explorer/tables` |
| CU-EX02 | Previsualizar filas paginadas | `/analytics/explorer/preview/{table}` |
| CU-EX03 | Filtrar/buscar tablas en UI | ExplorerComponent |
| CU-EX04 | Clasificar tablas por tipo (dim/fact/agg) | Explorer UI |

### Spec candidata **010 — Catalog Stewardship** (opcional / táctica)

| CU candidato | Descripción | Endpoints |
|--------------|-------------|-----------|
| CU-STW01 | Crear/actualizar/eliminar artista | POST/PUT/DELETE `/artists` |
| CU-STW02 | Crear/actualizar/eliminar género | POST/PUT/DELETE `/genres` |
| CU-STW03 | Crear/actualizar/eliminar track | POST/PUT/DELETE `/tracks` |
| CU-STW04 | Autenticar/autorizar steward | (nuevo; hoy sin auth) |

### Spec candidata **011 — Platform Health & API Transparency** (menor; puede fusionarse en 006 v2)

| CU candidato | Descripción | Endpoints |
|--------------|-------------|-----------|
| CU-PH01 | Consultar metadata API raíz | `GET /` |
| CU-PH02 | Health extendido con tablas/version | `GET /health` (ampliar **006**) |

**Total CU candidatos nuevos:** ~22 (sin contar extensiones a specs existentes).

---

## 7. Objetivos operativos (OO) afectados — propuesta de extensión

La matriz actual usa **OE-01** único y **OT-01…OT-06**. Funcionalidad sin spec requiere **nuevos OT/OO** (propuesta alineada Constitución §4.3):

| OT propuesto | OO propuesto | Dominio | GAPs |
|--------------|--------------|---------|------|
| **OT-07** | **OO-12** — Operar dashboards y analítica de consumo de catálogo | Analítica | A01–A07, D01–D03 |
| **OT-08** | **OO-13** — Operar pipeline de datos y generación sintética | Data Engineering | B01–B06 |
| **OT-08** | **OO-14** — Inspeccionar y explorar warehouse | Data Engineering | C01–C03 |
| **OT-09** | **OO-16** — Administrar catálogo (steward) | Catálogo táctico | E01–E03 |
| **OT-06** (ext.) | **OO-10** (ext.) — Transparencia health/API | Plataforma | F01–F02 |

**Nota:** OO-12…OO-14 **no existen** hoy en `TRACEABILITY-MASTER.md`. OO-15 ya asignado a audio features (**003**).

---

## 8. Riesgo de no documentarlos

| Riesgo | Severidad | Descripción |
|--------|-----------|-------------|
| **R-OG01** Brecha SDD Constitución §12 | Alta | Constitución exige trazabilidad; ~22 CU operativos sin OE→CA |
| **R-OG02** Synthetic sin gobernanza (P10) | Alta | POST synthetic sin spec CU/FR; solo disclaimer parcial **005** |
| **R-OG03** Engineer APIs sin auth backend | Alta | Explorer + synthetic accesibles vía API sin rol server-side |
| **R-OG04** CRUD catálogo sin auth ni spec | Alta | Mutaciones warehouse expuestas; **003** las excluye explícitamente |
| **R-OG05** Drift Home vs spec **004** | Media | KPIs analíticos en home no trazados a **004** |
| **R-OG06** Duplicidad dashboard/home/stats | Media | Tres pantallas consumen mismos endpoints sin delimitación |
| **R-OG07** Impl column inutilizable | Media | Nuevas features no podrán marcar Impl en matriz |
| **R-OG08** Auditoría plataforma incompleta | Alta | Informes 001–006 ~87% código consumo; ~0% analítica/ELT |
| **R-OG09** Onboarding operativo confuso | Media | Constitución §4.3 vs docs legacy vs UI real |
| **R-OG10** PocketBase/ELT CLI sin runbook spec | Media | Compose pipeline no tiene CU operativos |

---

## 9. Recomendación de nuevas specs (sin crearlas)

Prioridad sugerida para cierre de brecha operativa total:

| Prioridad | Spec propuesta | Título | OT | OO | Endpoints / rutas clave | Justificación |
|-----------|----------------|--------|----|----|-------------------------|---------------|
| **P1** | **007** | Operational Analytics & Dashboards | OT-07 | OO-12 | `/dashboard/analytics`, `/trending`, `/analytics`, `/comparativas`, stats summary/growth/top | Mayor superficie usuario autenticado; Constitución §3 In Scope analytics |
| **P1** | **008** | Data Pipeline & Synthetic Operations | OT-08 | OO-13 | `/elt-pipeline`, `/stats/synthetic*`, `/analytics/warehouse`, `/stats/loads`, ELT CLI | P10 synthetic boundary; rol engineer; deuda seguridad |
| **P2** | **009** | Warehouse Explorer & Inspection | OT-08 | OO-14 | `/explorer`, explorer API | Complemento 008; audiencia engineer/analyst |
| **P2** | **010** | Catalog Stewardship | OT-09 | OO-16 | POST/PUT/DELETE catalog | Código ya existe; spec **003** remite a “012” táctica |
| **P3** | **011** | Platform Health & API Metadata | OT-06 ext. | OO-10 ext. | `/`, `/health` | Pequeño; puede ampliar **006** en lugar de spec nueva |

### Alternativa de consolidación (menos specs)

| Opción | Specs | Trade-off |
|--------|-------|-----------|
| **A — Granular (recomendada)** | 007 + 008 + 009 + 010 | Trazabilidad clara; más `/speckit-plan` |
| **B — Dos specs** | **007 Analytics** (incl. explorer read-only) + **008 Data Ops** (ELT + synthetic + steward) | Menos overhead; OO mixtos |
| **C — Una spec** | **007 Platform Analytics & Data Ops** | Rápida pero viola principio dominio Constitución P2 |

### Acciones previas a redactar specs (no incluidas en este informe)

1. Ratificar OT-07…OT-09 y OO-12…OO-14 en Constitución o anexo táctico.
2. Decidir si **010** es operativa usuario o spec táctica API (spec **003** ya apunta a steward externo).
3. Extender `TRACEABILITY-MASTER.md` solo tras ratificación — evitar filas huérfanas.
4. Delimitar **004** Home vs **007** Dashboard (evitar overlap D01–D03).

---

## 10. Matriz de cobertura código vs specs 001–006

| Capa | Módulos código | Cubiertos 001–006 | Sin spec | % sin spec (módulos) |
|------|----------------|-------------------|----------|----------------------|
| Frontend rutas autenticadas | 18 rutas | 11 | 7 (+ parciales) | ~39% rutas |
| Backend endpoint groups | 8 grupos | 4 grupos plenos + 2 parciales | 2 grupos + CRUD | ~25% grupos |
| StatsService métodos | 16 | 3 | 13 | ~81% métodos |
| OO en matriz | 12 OO | 12 | 0 (+ 3–4 OO propuestos faltantes) | 0% matriz / ~35% plataforma |

**Interpretación:** El consumo musical está mayormente especificado; la **capa analítica y de data engineering representa la mayoría de la brecha operativa documental**.

---

## 11. Referencias cruzadas

| Artefacto | Declaración relevante |
|-----------|----------------------|
| `DOCUMENT-COVERAGE-REPORT.md` §7 | Trending/dashboards y DE UI fuera de 001–006 |
| `003-catalog-discovery/spec.md` | CRUD steward out of scope; remite spec táctica |
| `005-personalized-discovery/spec.md` | FR-RC05 synthetic disclaimer; no pipeline |
| `006-account-self-service/spec.md` | ST05 health; ST06 engineer tabs sin warehouse FR |
| Constitución §3.1 | Analytics, ELT UI, explorer en In Scope |
| Constitución P2 | Dominios: analytics, data-engineering separados |
| Constitución P10 | Synthetic boundary — requiere spec 008 |
| `TRACEABILITY-MASTER.md` | Alcance explícito: solo 001–006 |

---

**Elaborado por:** Auditoría SDD — análisis código vs specs  
**Estado:** Informe de brecha; **no** crea specs, planes ni tasks  
**Próximo paso sugerido (fuera de este documento):** Decisión arquitecto producto sobre opción A/B/C §9, luego `/speckit-specify` para 007 como P1.
