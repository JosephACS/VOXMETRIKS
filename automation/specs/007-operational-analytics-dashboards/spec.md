# Feature Specification: Analítica Operativa y Dashboards de Catálogo

**Feature Branch**: `007-operational-analytics-dashboards`  
**Feature Directory**: `specs/007-operational-analytics-dashboards/`  
**Created**: 2026-06-20  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de analítica de consumo de catálogo: dashboards KPI, trending, engagement, comparativas inter-género y widgets embebidos en Home y perfil.

**Prerrequisitos:** `001-user-identity-access`; `003-catalog-discovery` (metadata catálogo, `genres/stats`); warehouse DuckDB poblado con agregados analíticos (`agg_*`, `fact_streaming`, dimensiones).

**Delimitación vs otras specs (evitar duplicidad):**

| Dominio | Spec propietaria | Spec 007 |
|---------|------------------|----------|
| Auth / sesión / guards shell | 001 | ❌ Consume identidad |
| Catálogo browse/search/detalle track | 003 | ❌ Solo agregados y stats |
| Audio features track-level (OO-15) | 003 | ❌ Energy distribution es agregado cross-catálogo |
| Reproductor / cola / Home hub escucha | 004 | ❌ Play vía 004; Home rail KPI → 007 CU-AN08 |
| Playlists / favoritos CRUD | 002 | ❌ Favorite contextual desde trending |
| Recomendaciones / historial hub | 005 | ❌ |
| Perfil / settings UI core | 006 | ❌ Widgets analytics perfil → 007 CU-AN09 |
| Pipeline ELT / synthetic / explorer | 008–009 | ❌ |
| Stewardship CRUD catálogo | 010 | ❌ |

**Delimitación Constitución:** Analítica operativa consume **warehouse read-only** (P6). Métricas de plataforma/engagement derivadas de capa enterprise MAY incluir datos **synthetic** — MUST no presentarse como telemetría real del usuario individual (P10, alineado con 005).

---

## Contexto Empresarial

Voxmetriks unifica **experiencia musical personalizada** con **inteligencia analítica de catálogo** como propuesta de valor estratégica (Constitución §1–§2, OE-01). Tras identidad (001) y consumo de catálogo (003), usuarios autenticados y analistas de producto MUST poder **comprender el estado del catálogo**, **tendencias de popularidad**, **patrones de engagement** y **comparativas entre géneros** mediante dashboards operativos en la SPA.

La auditoría documental (`OPERATIVE-GAP-ANALYSIS.md`) confirmó implementación existente sin spec dedicada:

- Rutas UI: `/dashboard/analytics`, `/trending`, `/analytics`, `/comparatives`.
- Servicio `StatsService` con 13 métodos analíticos sin trazabilidad CU→FR.
- Consumo transversal: Home (`getSummary`, `getCatalogGrowth`), perfil (`getPlatformAnalytics`, `getTrendingAnalytics`), login (`getSummary`).
- Backend: routers `stats` y `analytics` (endpoints de consumo BI, excl. history/recommendations ya en **005**).

Constitución §3.1 incluye **analytics dashboards** en In Scope; §4.3 nivel operativo exige runbooks y health de capa analítica. Esta spec cierra la brecha SDD de la **capa analítica de consumo** — distinta de data engineering (**008**) y exploración warehouse (**009**).

Esta especificación gobierna la **capacidad operativa de Analítica y Dashboards**, definiendo comportamiento requerido del producto independiente de detalles de implementación Angular/FastAPI actuales.

---

## Problema

### Situación actual

Usuarios autenticados y stakeholders de producto necesitan:

1. **Visualizar** KPIs globales del catálogo (tracks, artistas, géneros, álbumes, popularidad, energía).
2. **Analizar** evolución temporal del catálogo y rankings de popularidad.
3. **Explorar** trending con streams diarios y distribución de popularidad.
4. **Consultar** métricas de engagement de plataforma (skip rate, completion, session time).
5. **Comparar** géneros mediante visualizaciones agregadas (radar, insights).
6. **Acceder** a resúmenes analíticos embebidos en Home y perfil sin duplicar lógica de negocio.

Riesgos sin especificación formal:

- Tres pantallas (Home, Dashboard, Trending) consumen `getSummary` sin delimitación con **004**.
- Widgets analíticos en `/users` mezclados con **006** OO-11 sin FR dedicados.
- APIs `stats/*` y `analytics/{trending,platform,engagement}` sin CU, RB ni CA auditables.
- Overlap energy distribution: agregado analítico vs audio features track-level (**003** OO-15) sin frontera documentada.
- Sin métricas empresariales M-12A–M-12D ni criterios de empty state warehouse vacío.

### Problema de negocio

**Voxmetriks no puede sostener su posicionamiento de "plataforma inteligente musical"** si la capa analítica operativa — visible en navegación principal y embebida en journeys críticos — carece de reglas empresariales, trazabilidad OE→HU y criterios de aceptación unificados. Producto, ingeniería y auditoría SDD operan con **comportamiento implícito** y **riesgo de drift** entre pantallas que comparten endpoints.

---

## Objetivo

Gobernar la **capacidad operativa de Analítica Operativa y Dashboards de Catálogo** en Voxmetriks:

1. Exponer dashboards KPI y evolución del catálogo vía API stats y UI dedicada.
2. Presentar trending tracks, streams diarios y acciones contextuales play/favorite.
3. Visualizar engagement, distribución de energía agregada y estadísticas por género.
4. Ofrecer comparativas inter-género basadas en agregados warehouse.
5. Definir contratos de widgets embebidos en Home (**004**) y perfil (**006**).
6. Garantizar estados vacío/degradado cuando warehouse no está poblado.
7. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU→FR→CA completa.

**Resultado esperado:** usuario autenticado explora analítica de catálogo con UX predecible, datos coherentes entre pantallas, integración play/favorite donde aplique, y transparencia sobre origen agregado/synthetic de métricas de plataforma.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Convertir Voxmetriks en plataforma de referencia que unifica experiencia musical personalizada con analítica de datos gobernada |
| **OT-07** | Objetivo Táctico | Habilitar capa analítica operativa de consumo de catálogo en SPA y API read-only |
| **OO-12** | Objetivo Operativo | Operar dashboards, trending, engagement y comparativas de catálogo para usuarios autenticados |
| **M-12A** | Meta | Panel analítico KPI carga ≤ 3 s p95 con warehouse poblado |
| **M-12B** | Meta | Trending muestra ≥ 10 tracks con datos cuando agregados existen |
| **M-12C** | Meta | Métricas engagement visibles con estado vacío degradado (no error opaco) |
| **M-12D** | Meta | 100 % rutas analíticas dedicadas accesibles a usuario autenticado estándar |
| **DEP-04** | Departamento | **Analítica de Producto** |
| **PKG-06** | Paquete | `analytics` (frontend `packages/analytics/`; backend `packages/analytics/routes/{stats,analytics}.py` — consumo BI) |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-AN01 | US-AN01 | FR-AN01 | CA-001 |
| CU-AN01 | US-AN01 | FR-AN08 | CA-001 |
| CU-AN01 | US-AN01 | FR-AN09 | CA-001 |
| CU-AN01 | US-AN01 | FR-AN24 | CA-001 |
| CU-AN02 | US-AN01 | FR-AN02 | CA-002 |
| CU-AN02 | US-AN01 | FR-AN10 | CA-002 |
| CU-AN07 | US-AN02 | FR-AN03 | CA-001 |
| CU-AN07 | US-AN02 | FR-AN11 | CA-001 |
| CU-AN03 | US-AN02 | FR-AN05 | CA-003 |
| CU-AN03 | US-AN02 | FR-AN12 | CA-003 |
| CU-AN03 | US-AN02 | FR-AN13 | CA-003 |
| CU-AN03 | US-AN02 | FR-AN17 | CA-006 |
| CU-AN03 | US-AN02 | FR-AN18 | CA-007 |
| CU-AN04 | US-AN03 | FR-AN07 | CA-004 |
| CU-AN04 | US-AN03 | FR-AN14 | CA-004 |
| CU-AN04 | US-AN03 | FR-AN04 | CA-004 |
| CU-AN04 | US-AN03 | FR-AN16 | CA-004 |
| CU-AN06 | US-AN03 | FR-AN06 | CA-004 |
| CU-AN06 | US-AN03 | FR-AN20 | CA-009 |
| CU-AN05 | US-AN04 | FR-AN15 | CA-005 |
| CU-AN05 | US-AN04 | FR-AN16 | CA-005 |
| CU-AN08 | US-AN05 | FR-AN01 | CA-008 |
| CU-AN08 | US-AN05 | FR-AN02 | CA-008 |
| CU-AN08 | US-AN05 | FR-AN19 | CA-008 |
| CU-AN09 | US-AN05 | FR-AN06 | CA-009 |
| CU-AN09 | US-AN05 | FR-AN05 | CA-009 |
| CU-AN09 | US-AN05 | FR-AN20 | CA-009 |
| CU-AN01 | US-AN06 | FR-AN21 | CA-010 |
| CU-AN03 | US-AN06 | FR-AN21 | CA-010 |
| CU-AN04 | US-AN06 | FR-AN21 | CA-010 |
| CU-AN05 | US-AN06 | FR-AN21 | CA-010 |
| CU-AN01 | US-AN06 | FR-AN22 | CA-011 |
| CU-AN03 | US-AN06 | FR-AN22 | CA-011 |
| CU-AN01 | US-AN01 | FR-AN23 | CA-001 |
| CU-AN01 | US-AN06 | FR-AN25 | CA-010 |
| CU-AN01 | US-AN01 | FR-AN26 | CA-011 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN02 | US-AN01 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN07 | US-AN02 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN03 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN06 | US-AN03 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN05 | US-AN04 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN08 | US-AN05 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN09 | US-AN05 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN01 | US-AN06 | 007 | Pendiente |
| OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN03 | US-AN06 | 007 | Pendiente |

---

## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Registrado Autenticado** | Consume dashboards, trending, analytics y comparativas en navegación principal | Entender catálogo; descubrir tendencias; play/favorite desde trending |
| **Analista de Producto** | Mismo actor operativo con foco en KPIs y comparativas | Validar salud catálogo; comparar géneros |
| **Usuario Visitante** | Sin sesión SPA; puede consumir stats summary en login showcase vía API | Vista previa plataforma antes de registro |
| **Sistema Voxmetriks** | Agrega warehouse; sirve APIs read-only; renderiza empty states | Cumplir P6 read-only; M-12A–D |
| **Capa Warehouse DuckDB** | Fuente de agregados dim/fact/agg | No actor UI — provee datos |

---

## Casos de Uso

### CU-AN01: Ver panel analítico KPI catálogo

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida; warehouse accesible o vacío |
| **Flujo principal** | 1. Usuario navega a `/dashboard/analytics` → 2. Sistema solicita summary → 3. UI renderiza KPI cards (canciones, artistas, géneros, álbumes, popularidad, energía) → 4. Usuario visualiza estado catálogo |
| **Postcondición** | KPIs visibles o empty state con mensaje orientador |
| **Flujo alternativo** | 2a. API error → UI muestra error degradado sin crash (FR-AN21) |
| **Flujo alternativo** | 3a. Preferencia showKpis=false → sección KPI oculta (FR-AN24) |
| **Reglas de negocio** | RB-AN01, RB-AN08 |

### CU-AN02: Ver evolución crecimiento catálogo

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | En dashboard analítico o Home embed |
| **Flujo principal** | 1. Sistema solicita catalog-growth (default 12 meses) → 2. UI renderiza serie temporal (sparkline/chart) → 3. Usuario interpreta tendencia |
| **Postcondición** | Gráfico visible o empty state si serie vacía |
| **Flujo alternativo** | 1a. Serie vacía → RB-AN09 empty state |
| **Reglas de negocio** | RB-AN01, RB-AN09 |

### CU-AN03: Ver trending tracks y streams diarios

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario abre `/trending` → 2. Sistema carga top-tracks y trending analytics → 3. UI lista tracks con ranking, popularidad, chart streams → 4. Usuario explora tendencias |
| **Postcondición** | Lista y chart visibles o empty state |
| **Flujo alternativo** | 4a. Usuario play track → invoca CU play 004 |
| **Flujo alternativo** | 4b. Usuario favorita → invoca CU favorito 002 |
| **Reglas de negocio** | RB-AN02, RB-AN10 |

### CU-AN04: Ver métricas engagement y energía agregada

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario abre `/analytics` → 2. Sistema carga energy-distribution, genre stats, engagement → 3. UI presenta barras energía, top géneros, KPIs engagement (skip rate, completion, score, session time) |
| **Postcondición** | Paneles analíticos visibles o parcialmente vacíos con degradación |
| **Flujo alternativo** | 2a. Engagement API falla → UI muestra géneros/energía disponibles (FR-AN21) |
| **Reglas de negocio** | RB-AN03, RB-AN01 |

### CU-AN05: Comparar géneros (radar e insights)

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN05 |
| **Actor principal** | Usuario Registrado Autenticado / Analista de Producto |
| **Precondición** | Sesión válida; genres/stats disponible |
| **Flujo principal** | 1. Usuario abre `/comparatives` → 2. Sistema carga genre stats (limit 30) → 3. UI renderiza radar popularidad/energía e insights agregados → 4. Usuario compara géneros |
| **Postcondición** | Visualización comparativa visible o empty state |
| **Flujo alternativo** | 2a. Sin géneros → empty state |
| **Reglas de negocio** | RB-AN06 |

### CU-AN06: Ver analytics de plataforma por dispositivo

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN06 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario accede a platform analytics (página analytics y/o perfil) → 2. Sistema solicita `/analytics/platform` → 3. UI muestra breakdown dispositivos/plataforma |
| **Postcondición** | Métricas plataforma visibles o empty con disclosure synthetic si aplica |
| **Flujo alternativo** | 2a. Datos synthetic → RB-AN04 disclosure |
| **Reglas de negocio** | RB-AN04, RB-AN01 |

### CU-AN07: Consumir top tracks por popularidad (stats)

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN07 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Warehouse con dim_track |
| **Flujo principal** | 1. Sistema solicita `/stats/top-tracks` con limit → 2. UI presenta ranking en dashboard y/o trending según pantalla |
| **Postcondición** | Top tracks visibles ordenados por popularidad |
| **Nota** | Distinto algoritmo/ranking que trending analytics (RB-AN02) |
| **Reglas de negocio** | RB-AN02, RB-AN10 |

### CU-AN08: Consumir rail analítico embebido en Home

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN08 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Usuario en `/dashboard` (Home hub, spec **004**) |
| **Flujo principal** | 1. Home carga summary y catalog-growth → 2. UI muestra rail/sección KPI warehouse → 3. Usuario ve snapshot catálogo sin navegar a analytics dedicado |
| **Postcondición** | Widgets embebidos coherentes con dashboard analítico |
| **Delimitación** | Hub escucha/biblioteca permanece en **004**; solo widgets KPI en **007** |
| **Reglas de negocio** | RB-AN05 |

### CU-AN09: Consumir widgets analíticos en perfil

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AN09 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Usuario en `/users` (spec **006** OO-11) |
| **Flujo principal** | 1. Perfil carga platform y/o trending summaries → 2. UI muestra widgets analíticos junto a identidad/biblioteca → 3. Usuario ve contexto plataforma |
| **Postcondición** | Widgets visibles o ocultos si API falla sin bloquear perfil |
| **Delimitación** | Identidad y stats biblioteca personal en **006**; widgets agregados plataforma en **007** |
| **Reglas de negocio** | RB-AN05, RB-AN04 |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-AN01 — Dashboard analítico KPI (Priority: P1)

Como **Usuario Registrado**, quiero **ver un panel con KPIs del catálogo y su evolución**, para **entender el estado global del warehouse musical**.

**Why this priority**: Entregable central OO-12; ruta `/dashboard/analytics` es punto de entrada analítico principal; materializa M-12A.

**Independent Test**: Usuario autenticado abre `/dashboard/analytics`; ve ≥ 4 KPI cards con valores numéricos o empty state; gráfico crecimiento visible si hay datos.

**Acceptance Scenarios**:

1. **Given** warehouse poblado, **When** usuario abre `/dashboard/analytics`, **Then** muestra KPIs: total tracks, artistas, géneros, álbumes, popularidad promedio, energía promedio (FR-AN09).
2. **Given** datos catalog-growth disponibles, **When** dashboard carga, **Then** visualiza serie temporal últimos 12 meses (FR-AN10).
3. **Given** top-tracks disponibles, **When** dashboard carga, **Then** muestra tabla/lista top tracks (FR-AN11).
4. **Given** preferencia UI showKpis=false, **When** dashboard carga, **Then** oculta grid KPI manteniendo resto paneles si configurado (FR-AN24).
5. **Given** warehouse vacío, **When** dashboard carga, **Then** KPIs en cero y mensaje empty state, sin error 500 (FR-AN21, RB-AN08).

**Maps to**: CU-AN01, CU-AN02, CU-AN07 | FR-AN01–FR-AN11, FR-AN24 | M-12A

---

### User Story US-AN02 — Trending y top tracks (Priority: P1)

Como **Usuario Registrado**, quiero **explorar tracks en tendencia con gráfico de streams**, para **descubrir contenido popular con contexto temporal**.

**Why this priority**: Segunda ruta analítica más visible en nav; integra play/favorite; cumple M-12B.

**Independent Test**: Abrir `/trending`; ≥ 1 track listado cuando warehouse poblado; chart streams renderizado; play activa reproductor.

**Acceptance Scenarios**:

1. **Given** usuario en `/trending`, **When** página carga, **Then** lista tracks con metadata (título, artista, popularidad) (FR-AN12).
2. **Given** trending analytics con daily_streams, **When** página carga, **Then** chart últimos 14 días visible (FR-AN13).
3. **Given** ≥ 10 tracks en warehouse, **When** trending carga, **Then** muestra ≥ 10 entradas o máximo disponible (M-12B).
4. **Given** track en lista, **When** usuario pulsa play, **Then** MusicPlayerService (004) reproduce (FR-AN17).
5. **Given** track no favorito, **When** usuario pulsa favorito, **Then** API favoritos (002) persiste (FR-AN18).

**Maps to**: CU-AN03, CU-AN07 | FR-AN03, FR-AN05, FR-AN12–FR-AN13, FR-AN17–FR-AN18 | M-12B

---

### User Story US-AN03 — Analytics profundo engagement y géneros (Priority: P1)

Como **Usuario Registrado**, quiero **ver engagement, distribución de energía y stats por género**, para **comprender patrones de consumo del catálogo**.

**Why this priority**: Completa triada analítica principal (`/analytics`); cumple M-12C.

**Independent Test**: Abrir `/analytics`; paneles energía, géneros y engagement visibles o empty degradado.

**Acceptance Scenarios**:

1. **Given** energy-distribution poblado, **When** analytics carga, **Then** barras por bucket energía visibles (FR-AN04, FR-AN14).
2. **Given** genres/stats disponible, **When** analytics carga, **Then** top géneros con tracks count y popularidad (FR-AN16).
3. **Given** engagement API responde, **When** analytics carga, **Then** muestra skip_rate, completion_rate, engagement_score, avg_session_time (FR-AN07).
4. **Given** engagement API falla, **When** analytics carga, **Then** muestra energía/géneros disponibles + indicador degradación (FR-AN21, M-12C).
5. **Given** platform analytics en misma sesión, **When** usuario consulta, **Then** breakdown dispositivo visible donde UI lo exponga (FR-AN06, FR-AN20).

**Maps to**: CU-AN04, CU-AN06 | FR-AN04, FR-AN07, FR-AN14, FR-AN16, FR-AN06 | M-12C

---

### User Story US-AN04 — Comparativas inter-género (Priority: P2)

Como **Analista de Producto**, quiero **comparar géneros en radar e insights**, para **identificar oportunidades de catálogo**.

**Why this priority**: Ruta especializada; depende de genres/stats estable (003).

**Independent Test**: Abrir `/comparatives`; radar con hasta 6 géneros top; insights numéricos visibles.

**Acceptance Scenarios**:

1. **Given** ≥ 3 géneros en stats, **When** comparatives carga, **Then** radar popularidad y energía renderizado (FR-AN15).
2. **Given** genre stats, **When** comparatives carga, **Then** insights: count géneros, popularidad media, energía media, total tracks (FR-AN16).
3. **Given** sin géneros, **When** comparatives carga, **Then** empty state claro.

**Maps to**: CU-AN05 | FR-AN15, FR-AN16 | M-12D

---

### User Story US-AN05 — Widgets embebidos Home y perfil (Priority: P2)

Como **Usuario Registrado**, quiero **ver resúmenes analíticos en Home y perfil**, para **acceder a contexto catálogo sin cambiar de sección**.

**Why this priority**: Cierra brecha cross-spec con 004/006; evita duplicación futura de FRs.

**Independent Test**: Home muestra KPI rail; perfil muestra widgets platform/trending; mismos valores que APIs dedicadas para mismo warehouse state.

**Acceptance Scenarios**:

1. **Given** usuario en `/dashboard` Home, **When** carga, **Then** rail KPI summary/growth visible según diseño Home (FR-AN19, CU-AN08).
2. **Given** usuario en `/users`, **When** perfil carga, **Then** widgets platform/trending no bloquean carga identidad (FR-AN20, CU-AN09).
3. **Given** API analytics falla en embed, **When** Home/perfil carga, **Then** sección embed oculta o degradada; resto página funcional (RB-AN05).

**Maps to**: CU-AN08, CU-AN09 | FR-AN19, FR-AN20 | M-12D

*Delimitación:* US-AN05 NO redefine Home hub escucha (**004** US-H01) ni perfil identidad (**006** US-PF01).

---

### User Story US-AN06 — Estados vacío, error y acceso (Priority: P1)

Como **Sistema Voxmetriks**, debo **degradar gracefully y restringir rutas analíticas dedicadas a usuarios autenticados**, para **cumplir M-12C/M-12D y P6 read-only**.

**Why this priority**: Transversal; sin esto analítica falla en entornos dev vacíos o sesión inválida.

**Independent Test**: Warehouse vacío → empty states; visitante → redirect login en rutas dedicadas; APIs stats no mutan warehouse.

**Acceptance Scenarios**:

1. **Given** DuckDB sin tablas o vacío, **When** cualquier pantalla analítica carga, **Then** empty/degraded state, no crash SPA (FR-AN21, RB-AN08).
2. **Given** visitante sin sesión, **When** navega a `/dashboard/analytics`, `/trending`, `/analytics`, `/comparatives`, **Then** redirect login (FR-AN22, CA-011).
3. **Given** visitante en login page, **When** showcase stats carga, **Then** summary API permitido sin auth (FR-AN23, alineado 001 RB-014).
4. **Given** operación analítica, **When** API procesa, **Then** zero mutaciones warehouse (FR-AN25, P6).
5. **Given** usuario autenticado, **When** abre shell, **Then** nav incluye entradas analíticas (FR-AN26).

**Maps to**: CU-AN01–AN05 (empty paths) | FR-AN21, FR-AN22, FR-AN23, FR-AN25, FR-AN26 | M-12C, M-12D

---

### Edge Cases

- **Warehouse degradado** (`/health` status degraded): analítica MUST mostrar empty state, no datos stale inventados.
- **Partial API failure**: Dashboard carga summary OK pero growth falla → panel growth empty, resto visible.
- **Limit parameter extremo**: top-tracks limit=0 o >100 → API MUST validar o clamp según plan.
- **Género con caracteres especiales**: comparatives radar labels MUST truncar/escapar sin romper SVG.
- **Track en trending sin audio demo**: play (004) MUST degradar según spec 004 edge cases.
- **Concurrent navigation**: usuario cambia ruta analítica mid-fetch → UI MUST cancelar/subscribir sin memory leak (plan).
- **i18n**: strings "En vivo", "Panel analítico" MUST existir en ES/EN.
- **showKpis toggle mid-session**: dashboard MUST reaccionar al cambiar preferencia 006 sin reload completo (plan).
- **Stats summary en login sin warehouse**: showcase muestra ceros o mensaje "datos no disponibles".
- **Platform metrics 100% synthetic**: disclosure badge MUST visible (RB-AN04, P10).

---

## Requirements *(mandatory)*

### Functional Requirements — API Stats

- **FR-AN01**: System MUST expose `GET /api/v1/stats/summary` returning aggregate catalog KPIs: total_tracks, total_artistas, total_generos, total_albumes, total_streams, average popularity, average energy.
- **FR-AN02**: System MUST expose `GET /api/v1/stats/catalog-growth` accepting optional `months` parameter returning temporal growth points.
- **FR-AN03**: System MUST expose `GET /api/v1/stats/top-tracks` accepting optional `limit` returning tracks ordered by popularity descending.
- **FR-AN04**: System MUST expose `GET /api/v1/stats/energy-distribution` (alias `/energia`) returning buckets of track counts by energy range.

### Functional Requirements — API Analytics (consumo)

- **FR-AN05**: System MUST expose `GET /api/v1/analytics/trending` accepting optional `limit` returning trending tracks and daily_streams series.
- **FR-AN06**: System MUST expose `GET /api/v1/analytics/platform` returning platform/device usage aggregates.
- **FR-AN07**: System MUST expose `GET /api/v1/analytics/engagement` returning skip_rate, completion_rate, engagement_score, avg_session_time_min.

### Functional Requirements — UI Dashboard

- **FR-AN08**: UI MUST provide authenticated route `/dashboard/analytics` (Panel analítico).
- **FR-AN09**: UI dashboard MUST display KPI cards sourced from summary API.
- **FR-AN10**: UI dashboard MUST display catalog growth chart sourced from catalog-growth API.
- **FR-AN11**: UI dashboard MUST display top tracks section sourced from top-tracks API.
- **FR-AN24**: UI dashboard MUST respect user UI preference `showKpis` when false hiding KPI grid.

### Functional Requirements — UI Trending

- **FR-AN12**: UI MUST provide authenticated route `/trending`.
- **FR-AN13**: UI trending MUST display daily streams chart from trending analytics API.
- **FR-AN17**: UI trending MUST integrate play action with music player (004).
- **FR-AN18**: UI trending MUST integrate favorite action with favorites API (002).

### Functional Requirements — UI Analytics & Comparatives

- **FR-AN14**: UI MUST provide authenticated route `/analytics`.
- **FR-AN15**: UI MUST provide authenticated route `/comparatives`.
- **FR-AN16**: UI analytics and comparatives MUST consume genre aggregate stats from catalog API (`GET /api/v1/genres/stats`) per spec 003.

### Functional Requirements — Embeds & Cross-cutting

- **FR-AN19**: Home hub (`/dashboard`, spec 004) MAY embed catalog summary and growth widgets using same API contracts (CU-AN08).
- **FR-AN20**: Profile UI (`/users`, spec 006) MAY embed platform and trending summary widgets (CU-AN09).
- **FR-AN21**: All analytics UI surfaces MUST handle empty warehouse and partial API failures with user-friendly empty/degraded states without unhandled exceptions.
- **FR-AN22**: Dedicated analytics SPA routes (`/dashboard/analytics`, `/trending`, `/analytics`, `/comparatives`) MUST require authenticated session (authGuard).
- **FR-AN23**: Stats summary API MAY be consumed without authentication for public showcase surfaces (e.g. login page) consistent with 001 RB-014.
- **FR-AN25**: Analytics API operations MUST NOT mutate warehouse ELT tables (read-only, Constitución P6).
- **FR-AN26**: Authenticated shell navigation MUST expose analytics section entries (dashboard analítico, trending, analytics, comparatives) to standard users.

### Non-Functional Requirements

- **NFR-AN01 (Performance)**: `/dashboard/analytics` initial load MUST complete ≤ 3 s p95 when warehouse populated (M-12A).
- **NFR-AN02 (Performance)**: `/trending` initial load MUST complete ≤ 3 s p95 (M-12B).
- **NFR-AN03 (Performance)**: `/analytics` initial load MUST complete ≤ 3 s p95.
- **NFR-AN04 (Performance)**: `/comparatives` initial load MUST complete ≤ 3 s p95.
- **NFR-AN05 (Data integrity)**: Analytics reads MUST NOT write to DuckDB warehouse tables (P6).
- **NFR-AN06 (i18n)**: Analytics UI strings MUST support ES/EN via platform i18n.
- **NFR-AN07 (UX)**: Analytics pages MUST show loading skeletons during data fetch.
- **NFR-AN08 (Reliability)**: API errors MUST surface as recoverable UI error states, not white screen.
- **NFR-AN09 (Accessibility — target)**: KPI values MUST be readable by screen readers (labels associated).
- **NFR-AN10 (Auditability)**: Feature MUST maintain traceability matrix OE→HU documented in this spec.

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-AN01** | Analytics KPIs and aggregates MUST be sourced from warehouse read-only queries; no client-side invention of metrics. |
| **RB-AN02** | Rankings from `/stats/top-tracks` and `/analytics/trending` MAY differ in ordering algorithm; both are valid product views. |
| **RB-AN03** | Energy distribution in `/analytics` is catalog-wide aggregate; track-level audio features remain domain of spec 003 OO-15. |
| **RB-AN04** | Platform and engagement metrics derived from enterprise synthetic layer MUST disclose synthetic/demo nature when presented (Constitución P10). |
| **RB-AN05** | Embedded widgets in Home and Profile MUST use identical API contracts as dedicated analytics pages for same metric types. |
| **RB-AN06** | Comparatives MUST use genre dimensional aggregates only (`genres/stats`); no arbitrary SQL from UI. |
| **RB-AN07** | Engineer-only routes (ELT, explorer) MUST NOT be specified in this feature — remain specs 008/009; analytics routes are standard-user accessible (M-12D). |
| **RB-AN08** | Empty or missing warehouse MUST yield zero KPIs and empty charts, not HTTP 500 on user-facing UI paths. |
| **RB-AN09** | Catalog growth series MAY be empty when insufficient temporal data; UI MUST show empty chart state. |
| **RB-AN10** | Play and favorite actions from analytics surfaces MUST reference valid catalog track IDs existing in warehouse (003). |
| **RB-AN11** | Analytics MUST NOT expose per-user warehouse telemetry as if collected from authenticated user's real behavior unless sourced from user's own local data (005 domain). |
| **RB-AN12** | Public stats summary on login MUST NOT expose personally identifiable information or per-user metrics. |

### Key Entities

- **StatsSummary**: total_tracks, total_artistas, total_generos, total_albumes, total_streams, avg_popularity, avg_energy (field names MAY alias in API contract).
- **CatalogGrowthPoint**: period (fecha/month), track_count or growth metric, optional streams.
- **TopTrack**: track_id, title, artist, popularity, album?, duration?, rank implicit by order.
- **EnergyDistributionBucket**: energy_range_label, cantidad_tracks, optional percentage.
- **TrendingAnalytics**: tracks[], daily_streams[{ fecha, total_streams }].
- **PlatformAnalytics**: devices[], platforms[], percentages or counts, source tag (warehouse|synthetic).
- **EngagementAnalytics**: skip_rate, completion_rate, engagement_score, avg_session_time_min.
- **GeneroPopularidad** (from 003): nombre_genero, total_tracks, popularidad_promedio, energia_promedio.
- **AnalyticsEmbedConfig**: surface (home|profile), metrics[], refreshPolicy (on-init).

---

## Criterios de Aceptación Globales (Feature)

La feature **007-operational-analytics-dashboards** se considera **aceptada operativamente** cuando:

1. **CA-001**: `/dashboard/analytics` operativo con KPIs, growth y top tracks o empty state coherente.
2. **CA-002**: Gráfico catalog-growth visible en dashboard cuando datos existen.
3. **CA-003**: `/trending` operativo con lista tracks, chart streams, play y favorite integrados.
4. **CA-004**: `/analytics` operativo con energía, géneros y engagement (degradación parcial aceptada).
5. **CA-005**: `/comparatives` operativo con radar/insights de géneros.
6. **CA-006**: Play desde trending activa reproductor 004 con track correcto.
7. **CA-007**: Favorite desde trending persiste vía API 002.
8. **CA-008**: Home embed KPI rail trazado a CU-AN08 sin duplicar FRs de hub escucha 004.
9. **CA-009**: Profile widgets analíticos trazados a CU-AN09 sin bloquear perfil 006.
10. **CA-010**: Warehouse vacío produce empty states en 100% pantallas analíticas (smoke test).
11. **CA-011**: Rutas dedicadas analíticas requieren autenticación; visitante redirect login.
12. **CA-012**: Matriz trazabilidad OE→HU→FR→CA completa documentada en spec.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-AN01**: 95% cargas `/dashboard/analytics` completan ≤ 3 s p95 con warehouse demo poblado (M-12A).
- **SC-AN02**: 90% sesiones con warehouse poblado muestran ≥ 10 tracks en `/trending` (M-12B).
- **SC-AN03**: 100% pantallas analíticas con warehouse vacío muestran empty state sin error JS no capturado (M-12C).
- **SC-AN04**: 100% intentos acceso directo URL analítica sin sesión resultan redirect login (M-12D).
- **SC-AN05**: 0 mutaciones warehouse en suite pruebas read-only analytics APIs (NFR-AN05).
- **SC-AN06**: 100% filas matriz CU→FR→CA en spec 007 con Impl actualizable en TRACEABILITY-MASTER post-ratificación.

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-AN01 | Overlap Home KPIs vs spec 004 sin enmienda | Media | Medio | CU-AN08, FR-AN19, delimitación explícita; enmienda 004 v1.1 futura |
| R-AN02 | Overlap perfil widgets vs spec 006 | Media | Medio | CU-AN09, FR-AN20; enmienda 006 v1.1 futura |
| R-AN03 | Usuario interpreta engagement synthetic como comportamiento real | Media | Alto | RB-AN04, RB-AN11, P10 |
| R-AN04 | Duplicidad summary en login, Home, Dashboard | Alta | Bajo | RB-AN05 contratos API únicos; UX diferenciada por superficie |
| R-AN05 | Energy distribution confundido con OO-15 audio features | Media | Medio | RB-AN03 delimitación 003 |
| R-AN06 | top-tracks vs trending rankings inconsistentes confunden usuario | Media | Bajo | RB-AN02 documentado; tooltips en plan |
| R-AN07 | Warehouse vacío en dev bloquea demos analíticas | Alta | Medio | RB-AN08, FR-AN21 empty states |
| R-AN08 | StatsService mezcla métodos 008/009 sin frontera | Media | Alto | PKG-06 vs PKG-07 en specs 008/009; 007 solo métodos consumo |
| R-AN09 | Performance degradada con warehouse grande | Baja | Medio | NFR-AN01–04; agregados precomputados agg_* |
| R-AN10 | 001 RB-014 (analytics anónimo) vs FR-AN22 (rutas auth) | Media | Bajo | FR-AN23 API pública selectiva; SPA routes autenticadas |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| `001-user-identity-access` | Hard | Sesión autenticada; authGuard; clasificación rutas |
| `003-catalog-discovery` | Hard | genres/stats; track IDs válidos; metadata catálogo |
| `004-listening-experience` | Soft | Play desde trending; delimitación Home hub |
| `002-personal-music-library` | Soft | Favorite desde trending |
| `006-account-self-service` | Soft | showKpis preference; profile embed surface |
| Warehouse DuckDB poblado | Hard | Agregados dim_*, fact_*, agg_* |
| `StatsService` / analytics routes | Hard | Contratos API existentes |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | P2 dominio analytics, P6 read-only, P10 synthetic, §12 trazabilidad |
| `OPERATIVE-GAP-ANALYSIS.md` | Origen brecha GAP-A01–A07, D01–D04 |
| `TRACEABILITY-MASTER.md` | Integración filas 007 post-ratificación OT-07/OO-12 |
| Spec Kit workflow | Plan/tasks vía `/speckit-plan` |

### Dependencias externas

| Dependencia | Descripción |
|-------------|-------------|
| Ninguna CDN analytics externo | Toda analítica desde DuckDB local |
| Ningún BI third-party | Dashboards nativos SPA |

### Specs downstream (007 habilita)

| Spec | Relación |
|------|----------|
| `008-data-pipeline-synthetic-operations` | Pipeline alimenta agregados consumidos por 007 |
| `010-catalog-stewardship` | Mutaciones catálogo afectan KPIs 007 |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§2 Propuesta de valor** | Analítica gobernada como diferenciador OE-01 |
| **§3.1 In Scope** | Analytics dashboards explícitamente incluidos |
| **§4.3 Nivel Operativo** | Dashboards operativos día a día usuario/analista |
| **§5 P2 Package-by-Domain** | PKG-06 analytics exclusivo |
| **§5 P6 Warehouse vs App** | FR-AN25, NFR-AN05: reads warehouse; no app_user |
| **§5 P10 Synthetic boundary** | RB-AN04, RB-AN11 engagement/platform |
| **§12 Trazabilidad** | Matriz OE→Impl en spec |
| **§14 Nomenclatura** | Branch `007-operational-analytics-dashboards` |
| **§15 Reglas Specs** | Spec operativa consumo BI, no ELT |

---

## Out of Scope

- Pipeline ELT, generación synthetic, estado warehouse UI (**008**)
- Explorer tablas warehouse (**009**)
- CRUD steward catálogo (**010**)
- Health API root metadata (**011** o extensión **006**)
- Recomendaciones e historial hub (**005**)
- Reproductor/controles/cola (**004** excepto invocación play)
- Playlists/favoritos CRUD (**002** excepto invocación favorite)
- Catálogo browse/search/detalle (**003** excepto genres/stats)
- Registro/login/guards fundacionales (**001** excepto consumo)
- Perfil/settings UX core (**006** excepto embed widgets)
- Export CSV/PDF reportes
- Alertas/notificaciones analíticas
- ML forecasting / predicción series temporales
- Real-time streaming analytics (Kafka, websockets)

---

## Assumptions

- Warehouse contiene al menos dimensiones `dim_track`, `dim_artista`, `dim_genero` tras ELT exitoso.
- Agregados `agg_genero_popularidad`, `agg_distribucion_energia` existen o API calcula equivalente on-the-fly.
- Usuario autenticado estándar (no engineer) es audiencia principal rutas 007 (RB-AN07).
- Entorno dev puede operar con warehouse vacío — empty states son aceptables.
- `environment.apiUrl` apunta a API Voxmetriks operativa.
- Preferencia `showKpis` existe en UiPreferencesService (006) o default true.
- Audio demo para play desde trending sigue restricciones spec 004 (no streaming real).
- Idiomas ES/EN suficientes para UI analítica inicial.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — `/speckit-specify`  
**Next Step**: `/speckit-clarify` (opcional) → `/speckit-checklist` → `/speckit-plan` — Constitution Check P6, P10; delimitación contracts con 004/006.
