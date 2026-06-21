# Feature Specification: Descubrimiento y Consumo de Catálogo Musical

**Feature Branch**: `003-catalog-discovery`  
**Feature Directory**: `specs/003-catalog-discovery/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de consumo de catálogo musical: artistas, géneros, tracks, búsqueda y exploración de audio features.

**Prerrequisitos:** Warehouse poblado (capa datos); spec **001** para acciones personalizadas (favorito/playlist) en contexto autenticado.

**Delimitación vs 002:** Esta spec NO define playlists ni favoritos — solo **lectura y navegación** del catálogo más búsqueda. Acciones personalizadas invocan dominio 002.

**Delimitación vs 001:** Navegación catálogo MAY ser accesible en shell autenticado; esta spec NO redefine guards globales.

---

## Contexto Empresarial

Voxmetriks entrega valor fundamental mediante **acceso operativo al catálogo musical** derivado del warehouse dimensional (Constitución §1, §8). Usuarios finales MUST poder explorar artistas, géneros y tracks, buscar contenido y comprender atributos musicales (audio features) para decisiones de escucha y personalización.

La auditoría identificó **21 endpoints** de catálogo (artists, genres, tracks), rutas UI `/artists`, `/genres`, `/tracks`, `/tracks/:id`, `/search`, `/audio-features`, y warehouse `dim_*` con features inline en `dim_track`. El catálogo es **prerrequisito** de specs 002, 004, 005 y 008.

Constitución §3.1 incluye catálogo CRUD en alcance; esta spec define **consumo operativo** para usuario final. Mutaciones CRUD de catálogo (POST/PUT/DELETE sin auth) se documentan como **capacidad de steward** fuera del actor principal — ver Out of Scope operativo usuario.

---

## Problema

Sin especificación formal del dominio catálogo:

- No hay trazabilidad OE→HU para journeys de descubrimiento.
- Búsqueda vs listado vs detalle no tienen criterios de aceptación unificados.
- Audio features (inline en `dim_track`) carecen de reglas de presentación empresarial.
- Integración con favoritos/playlists (002) y reproductor (004) no tiene contrato documentado.

**Problema de negocio:** usuarios no pueden **descubrir y evaluar** contenido musical de forma predecible si el catálogo no está gobernado como capacidad operativa.

---

## Objetivo

Gobernar **Descubrimiento y Consumo de Catálogo Musical**:

1. Navegar artistas, géneros, tracks con paginación y filtros.
2. Consultar detalle de track con metadata y audio features.
3. Buscar tracks por texto.
4. Explorar distribución y significado de audio features a nivel catálogo.
5. Habilitar acciones contextuales (favorito, playlist, play) vía integración con specs 002/004.

---

## Trazabilidad Empresarial

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Estratégico | Plataforma inteligencia musical unificada |
| **OT-03** | Táctico | Exponer catálogo dimensional warehouse vía API y UI consumible |
| **OO-04** | Operativo | Navegar y consumir catálogo musical (artistas, géneros, tracks) |
| **OO-05** | Operativo | Buscar tracks en catálogo por criterios textuales |
| **OO-15** | Operativo | Explorar audio features del catálogo para descubrimiento |
| **M-4A** | Meta | 100% rutas catálogo UI cargan datos warehouse en ≤ 3s p95 (dev) |
| **M-4B** | Meta | Búsqueda retorna resultados relevantes en ≤ 2s p95 |
| **M-4C** | Meta | Detalle track incluye audio features cuando existen en warehouse |
| **DEP-02** | Departamento | **Producto Streaming** |
| **PKG-02** | Paquete | `streaming` (artists, genres, tracks, search, audio-features) |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-C01 | US-C01 | FR-C01 | CA-001 |
| CU-C02 | US-C01 | FR-C02 | CA-001 |
| CU-C03 | US-C01 | FR-C03 | CA-001 |
| CU-C03 | US-C01 | FR-C04 | CA-001 |
| CU-C04 | US-C02 | FR-C07 | CA-001 |
| CU-C05 | US-C02 | FR-C08 | CA-001 |
| CU-C05 | US-C02 | FR-C09 | CA-001 |
| CU-C05 | US-C02 | FR-C10 | CA-003 |
| CU-C06 | US-C01 | FR-C05 | CA-001 |
| CU-C06 | US-C01 | FR-C06 | CA-001 |
| CU-C04 | US-C02 | FR-C11 | CA-001 |
| CU-C01 | US-C01 | FR-C12 | CA-004 |
| CU-S01 | US-S01 | FR-S01 | CA-002 |
| CU-S02 | US-S01 | FR-S02 | CA-002 |
| CU-S01 | US-S01 | FR-S03 | CA-002 |
| CU-S02 | US-S01 | FR-S04 | CA-002 |
| CU-S03 | US-S01 | FR-S01 | CA-002 |
| CU-AF01 | US-AF01 | FR-AF01 | CA-003 |
| CU-AF01 | US-AF01 | FR-AF02 | CA-003 |
| CU-AF02 | US-C02 | FR-C10 | CA-003 |
| CU-AF01 | US-AF01 | FR-AF03 | CA-003 |
| CU-C05 | US-C03 | FR-C13 | CA-005 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C01 | US-C01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C02 | US-C01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C03 | US-C01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C04 | US-C02 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4C | DEP-02 | PKG-02 | CU-C05 | US-C02 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C06 | US-C01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S01 | US-S01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S02 | US-S01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S03 | US-S01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF01 | US-AF01 | 003 | Pendiente |
| OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF02 | US-C02 | 003 | Pendiente |
| OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C05 | US-C03 | 003 | Pendiente |


---
## Actores

| Actor | Descripción |
|-------|-------------|
| **Usuario Registrado** | Navega catálogo en shell autenticado; usa acciones personalizadas |
| **Usuario Visitante** | *Fuera shell actual* — catálogo accesible vía API sin auth; UI requiere auth por 001 |
| **Sistema Voxmetriks** | Sirve datos catálogo desde warehouse |
| **Data Steward** | CRUD catálogo (fuera actor principal v1) |


## Casos de Uso

### CU-C01: Listar artistas paginado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C01 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Warehouse catálogo poblado |
| **Flujo principal** | 1. Usuario abre listado artistas → 2. Sistema consulta dim con paginación → 3. UI muestra resultados |
| **Postcondición** | Lista artistas visible |
| **Flujo alternativo** | 2a. Warehouse vacío → empty state |
| **Reglas de negocio** | RB-C01, RB-C03 |

### CU-C02: Ver top artistas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C02 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Datos agregados disponibles |
| **Flujo principal** | 1. Usuario solicita ranking → 2. Sistema retorna top por popularidad |
| **Postcondición** | Ranking visible |
| **Flujo alternativo** | 2a. Sin datos → empty state |
| **Reglas de negocio** | RB-C01 |

### CU-C03: Listar géneros paginado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C03 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Catálogo poblado |
| **Flujo principal** | 1. Usuario abre géneros → 2. Sistema pagina dim géneros → 3. Opcional stats |
| **Postcondición** | Lista géneros visible |
| **Flujo alternativo** | 2a. Filtro búsqueda vacío → lista completa paginada |
| **Reglas de negocio** | RB-C03 |

### CU-C04: Listar tracks paginado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C04 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Catálogo poblado |
| **Flujo principal** | 1. Usuario abre tracks → 2. Sistema aplica filtros artista/género → 3. Retorna página |
| **Postcondición** | Lista tracks visible |
| **Flujo alternativo** | 2a. Filtros sin match → empty state |
| **Reglas de negocio** | RB-C01, RB-C03 |

### CU-C05: Ver detalle track

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C05 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Track ID válido |
| **Flujo principal** | 1. Usuario abre detalle → 2. Sistema join artista/género/features → 3. UI renderiza |
| **Postcondición** | Detalle completo visible |
| **Flujo alternativo** | 2a. ID inválido → 404 |
| **Reglas de negocio** | RB-C01, RB-C05 |

### CU-C06: Ver stats artista

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-C06 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Artista existe |
| **Flujo principal** | 1. Usuario solicita stats → 2. Sistema agrega métricas warehouse |
| **Postcondición** | Stats artista visibles |
| **Flujo alternativo** | 2a. Artista inexistente → 404 |
| **Reglas de negocio** | RB-C01 |

### CU-S01: Buscar tracks por texto

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-S01 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Query ≥ longitud mínima |
| **Flujo principal** | 1. Usuario ingresa término → 2. Sistema busca en catálogo → 3. Retorna resultados |
| **Postcondición** | Resultados búsqueda visibles |
| **Flujo alternativo** | 2a. Query corta → mensaje validación (RB-S01) |
| **Reglas de negocio** | RB-S01, RB-C04 |

### CU-S02: Ver resultados búsqueda

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-S02 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Búsqueda ejecutada |
| **Flujo principal** | 1. Usuario revisa lista → 2. Selecciona track → 3. Navega detalle o play |
| **Postcondición** | Usuario accede track desde búsqueda |
| **Flujo alternativo** | 2a. Sin resultados → empty state (FR-S04) |
| **Reglas de negocio** | RB-S01 |

### CU-S03: Registrar búsqueda en historial

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-S03 |
| **Actor principal** | Sistema Voxmetriks |
| **Precondición** | Búsqueda completada; usuario autenticado |
| **Flujo principal** | 1. Sistema registra query local → 2. Hub warehouse complementa (005) |
| **Postcondición** | Entrada historial búsqueda disponible |
| **Flujo alternativo** | 2a. Hub falla → solo local (005 FR-HI08) |
| **Reglas de negocio** | RB-S01 |

### CU-AF01: Explorar distribución audio features

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AF01 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Agregados warehouse disponibles |
| **Flujo principal** | 1. Usuario abre vista features → 2. Sistema sirve agregados → 3. UI visualiza |
| **Postcondición** | Distribución visible |
| **Flujo alternativo** | 2a. Sin agregados → empty state |
| **Reglas de negocio** | RB-AF01, RB-C02 |

### CU-AF02: Consultar features de track

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-AF02 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Track con features en dim |
| **Flujo principal** | 1. Usuario ve detalle → 2. Sistema expone features inline |
| **Postcondición** | Features track visibles |
| **Flujo alternativo** | 2a. Sin features → sección vacía graceful |
| **Reglas de negocio** | RB-C02 |

---


## User Scenarios & Testing *(mandatory)*

### User Story US-C01 — Explorar artistas y géneros (Priority: P1)

Como **Usuario Registrado**, quiero **navegar listas de artistas y géneros**, para **descubrir música por categoría**.

**Independent Test**: Paginar `/artists` y `/genres`; abrir detalle relacionado.

**Acceptance Scenarios**:

1. **Given** catálogo poblado, **When** abre `/artists`, **Then** ve lista paginada con nombres.
2. **Given** `/artists`, **When** aplica búsqueda, **Then** lista filtrada.
3. **Given** `/genres`, **When** carga stats, **Then** ve popularidad/energía agregada por género.
4. **Given** artista, **When** ve stats, **Then** muestra métricas warehouse.

**Maps to**: CU-C01, CU-C03, CU-C06 | FR-C01–C06

---

### User Story US-C02 — Explorar tracks y detalle (Priority: P1)

Como **Usuario Registrado**, quiero **listar tracks y ver detalle completo**, para **decidir qué escuchar**.

**Acceptance Scenarios**:

1. **Given** `/tracks`, **When** pagina y filtra por artista/género, **Then** resultados coherentes.
2. **Given** track ID, **When** abre `/tracks/:id`, **Then** ve nombre, artista, álbum, features.
3. **Given** detalle, **When** features existen, **Then** muestra danceability, energy, valence, etc.
4. **Given** track inexistente, **When** solicita detalle, **Then** error 404 claro.

**Maps to**: CU-C04, CU-C05, CU-AF02 | FR-C07–C12

---

### User Story US-S01 — Buscar música (Priority: P1)

Como **Usuario Registrado**, quiero **buscar tracks por nombre o artista**, para **encontrar canciones rápidamente**.

**Acceptance Scenarios**:

1. **Given** `/search`, **When** ingresa término ≥ 2 caracteres, **Then** resultados en ≤ 2s.
2. **Given** resultados, **When** selecciona track, **Then** navega a detalle o reproduce (004).
3. **Given** sin resultados, **Then** empty-state con sugerencia.

**Maps to**: CU-S01–S02 | FR-S01–S04

---

### User Story US-AF01 — Explorar audio features (Priority: P2)

Como **Usuario Registrado**, quiero **visualizar distribución de audio features del catálogo**, para **entender características musicales globales**.

**Acceptance Scenarios**:

1. **Given** `/audio-features`, **When** carga, **Then** visualiza distribución (ej. energía) desde warehouse.
2. **Given** feature seleccionada, **When** explora, **Then** datos consistentes con `agg_distribucion_energia` o inline dims.

**Maps to**: CU-AF01 | FR-AF01–AF03

---

### User Story US-C03 — Acciones contextuales desde catálogo (Priority: P2)

Como **Usuario Registrado**, quiero **favoritar, añadir a playlist o reproducir** desde catálogo, para **actuar sobre lo descubierto**.

**Acceptance Scenarios**:

1. **Given** track en listado, **When** toggle favorito, **Then** invoca spec 002 sin error.
2. **Given** track, **When** add to playlist, **Then** invoca spec 002.
3. **Given** track, **When** play, **Then** invoca spec 004 reproductor.

**Maps to**: Integración 002/004 — FR-C13

---

### Edge Cases

- Warehouse vacío: empty states; mensaje ejecutar ELT.
- Paginación límites: page/limit MUST tener máximos razonables.
- Caracteres especiales en búsqueda: sanitización sin error SQL (parametrized).
- Track sin features: detalle MUST mostrar catálogo sin bloque features vacío graceful.
- Schema drift columnas: backend MUST usar introspection (Constitución P5).

---

## Requirements *(mandatory)*

### Functional Requirements — Catálogo

- **FR-C01**: System MUST list artists with pagination and optional search.
- **FR-C02**: System MUST return top artists by popularity metric.
- **FR-C03**: System MUST return artist by ID with 404 if missing.
- **FR-C04**: System MUST list genres with pagination and optional search.
- **FR-C05**: System MUST return genre stats aggregation when requested.
- **FR-C06**: System MUST return artist stats for valid artist ID.
- **FR-C07**: System MUST list tracks with pagination, search, genre_id, artist_id filters.
- **FR-C08**: System MUST return track by ID.
- **FR-C09**: System MUST return track detail with joined artist, genre, album, audio features.
- **FR-C10**: System MUST return audio features for track when available.
- **FR-C11**: UI MUST provide routes `/artists`, `/genres`, `/tracks`, `/tracks/:id`.
- **FR-C12**: UI MUST display pagination controls for list views.
- **FR-C13**: UI MUST expose favorite, add-to-playlist, play actions on track rows (002, 004).

### Functional Requirements — Búsqueda

- **FR-S01**: System MUST search tracks by text query returning ranked/list results.
- **FR-S02**: UI MUST provide `/search` with input and results list.
- **FR-S03**: Search MUST require minimum query length (≥ 2 chars) or document behavior.
- **FR-S04**: Empty results MUST show user-friendly message.

### Functional Requirements — Audio Features

- **FR-AF01**: UI MUST provide `/audio-features` exploration view.
- **FR-AF02**: System MUST serve energy distribution or equivalent aggregation for visualization.
- **FR-AF03**: Presentation MUST label metrics clearly (energy, danceability, tempo, etc.).

### Non-Functional Requirements

- **NFR-01**: List endpoints ≤ 3s p95 paginated (≤ 50 items/page default).
- **NFR-02**: Search ≤ 2s p95 on standard dataset.
- **NFR-03**: Responses MUST use schema introspection; no hard-coded column failures (P5).
- **NFR-04**: API responses MUST align with `api.models.ts` types (P9).
- **NFR-05**: Catálogo read endpoints MAY be unauthenticated at API level; UI access governed by 001 shell.

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-C01** | Track MUST belong to catalog warehouse `dim_track`. |
| **RB-C02** | Audio features MUST read from inline columns o agg; NO `fact_audio_features` separada (Constitución §20). |
| **RB-C03** | Paginación MUST usar page≥1, limit acotado (ej. max 100). |
| **RB-C04** | Búsqueda MUST ser case-insensitive o documentar sensitivity. |
| **RB-C05** | Detalle MUST NOT exponer datos PII — solo metadata musical. |
| **RB-S01** | Búsqueda vacía MUST NOT retornar catálogo completo sin intención. |
| **RB-AF01** | Visualizaciones MUST indicar si datos son agregados warehouse vs track-level. |

### Key Entities

- **Artist (Artista)**: id, name, stats derivados.
- **Genre (Género)**: id, name, popularity aggregates.
- **Track**: id, name, spotify_id, artist, genre, album, popularity, duration.
- **AudioFeatures**: energy, danceability, valence, tempo, acousticness, instrumentalness, liveness, speechiness, loudness, key, mode.
- **SearchResult**: subset track fields optimized for list display.

---

## Criterios de Aceptación Globales

- **CA-001**: Navegación completa artists/genres/tracks/detalle funcional.
- **CA-002**: Búsqueda retorna resultados y navega a detalle/play.
- **CA-003**: Audio features visibles en detalle y pantalla exploración.
- **CA-004**: Paginación y filtros operativos.
- **CA-005**: Acciones 002/004 integradas en track rows.
- **CA-006**: Empty states cuando warehouse vacío.

---

## Success Criteria *(mandatory)*

- **SC-001**: 90% usuarios encuentran track buscado en ≤ 3 intentos búsqueda.
- **SC-002**: 100% detalles track existentes incluyen artista y género resueltos.
- **SC-003**: ≤ 3s p95 carga listados paginados en entorno dev estándar.
- **SC-004**: 0 errores SQL por column mismatch en queries catálogo (introspection).

---

## Riesgos

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-001 | Warehouse vacío | Health/ELT messaging |
| R-002 | CRUD catálogo sin auth (deuda) | Out of scope usuario; spec táctica 012 |
| R-003 | Search history split local/API | Spec 005 unifica |
| R-004 | schema.sql legacy vs dim_track | Plan: DDL authority elt |

---

## Dependencias

| Spec/Sistema | Tipo |
|--------------|------|
| Warehouse poblado | Hard (TA-04, TA-05) |
| 001-user-identity-access | Soft (UI shell) |
| 002-personal-music-library | Soft (acciones) |
| 004-listening-experience | Soft (play) |

---

## Relación Constitución v1.0.0

| Referencia | Aplicación |
|------------|------------|
| P2, P5, P9 | Package streaming, introspection, contracts |
| §8 Estrategia datos | Read from Gold warehouse |
| §20 Warehouse rules | Features inline dim_track |
| §3 Out scope streaming real | Play delegates 004 |

---

## Out of Scope

- CRUD steward catálogo (spec táctica API platform)
- Playlists/favoritos (002)
- Reproductor (004)
- Recomendaciones (005)
- Analytics enterprise dashboards (007)

---

## Assumptions

- ELT pipeline ejecutado al menos una vez.
- Usuario accede catálogo vía shell autenticado (001).
- Dataset estilo Spotify en warehouse.

---

**Next Step**: `/speckit-plan`
