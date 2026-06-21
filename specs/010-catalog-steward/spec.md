# Feature Specification: Catalog Steward — Administración de Catálogo

**Feature Branch**: `010-catalog-steward`  
**Feature Directory**: `specs/010-catalog-steward/`  
**Created**: 2026-06-20  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de administración y mantenimiento del catálogo musical warehouse: operaciones CRUD (crear, editar, eliminar) sobre artistas, géneros y tracks vía API y modales UI en rutas de catálogo existentes.

**Prerrequisitos:** `001-user-identity-access` (sesión, `authGuard`); warehouse DuckDB con dimensiones `dim_artista`, `dim_genero`, `dim_track`; spec **003** para consumo/descubrimiento read-only en mismas rutas.

**Evidencia base:** `SPEC-008-011-EVIDENCE-AUDIT.md` v1.0.0 (2026-06-20); código `routes/{artists,genres,tracks}.py`, `packages/streaming/*`, servicios FE. Esta spec **no** introduce capacidades ausentes en código.

---

## Delimitación obligatoria: Spec 003 vs Spec 010

Las rutas `/artists`, `/genres` y `/tracks` comparten **superficie UI** pero **responsabilidades documentales distintas**:

| Aspecto | Spec **003** — Consumo y descubrimiento | Spec **010** — Administración (steward) |
|---------|----------------------------------------|----------------------------------------|
| **Propósito** | Navegar, buscar, descubrir catálogo | Crear, editar, eliminar entidades catálogo |
| **Actor principal** | Usuario registrado (consumo) | Usuario autenticado con acceso modales CRUD *(rol steward dedicado **no** implementado)* |
| **Operaciones HTTP** | GET (list, detail, search, stats, top) | POST, PUT, DELETE |
| **UI** | Tablas, búsqueda, paginación, top artists, stats géneros, track-row play | Modales create/edit/delete, formularios, botones acción fila |
| **Endpoints ejemplo** | `GET /artists`, `GET /tracks/search`, `GET /genres/stats` | `POST/PUT/DELETE /artists`, `/genres`, `/tracks` |
| **CU propietarios** | CU-C* (003) | CU-CS* (010) |
| **Mutaciones warehouse** | ❌ Out of Scope 003 | ✅ In Scope 010 |

**Regla de no duplicidad:** Spec **003** MUST NOT redefinir FR de mutación. Spec **010** MUST NOT redefinir FR de browse/search/play salvo como **contexto de pantalla** donde ocurren modales steward.

**Estado actual código (evidencia):** CRUD accesible a **cualquier usuario autenticado** (`authGuard` únicamente); **no** existe `stewardGuard` ni auth backend en mutaciones (deuda P11).

---

## Contexto Empresarial

Voxmetriks mantiene catálogo musical en dimensiones warehouse DuckDB (Constitución §3.1 — catálogo CRUD in scope; P6 warehouse vs app). Operadores de catálogo MUST poder **administrar** artistas, géneros y tracks para mantener coherencia del warehouse — distinto del **consumo** documentado en **003**.

La auditoría (`SPEC-008-011-EVIDENCE-AUDIT.md`) confirmó implementación CRUD end-to-end ~88 %; gobernanza steward ~30 %:

- Backend: POST/PUT/DELETE en `artists.py`, `genres.py`, `tracks.py` con `get_write_conn`.
- Frontend: modales CRUD en `ArtistsComponent`, `GenresComponent`, `TracksComponent`.
- Servicios: `ArtistsService`, `GenresService`, `TracksService` métodos create/update/delete.
- **Ausente:** rol steward, auth backend mutaciones, auditoría `ctl_auditoria`, pantalla steward separada.

Spec **003** declara Out of Scope steward CRUD (L465). Esta spec cierra la brecha SDD de **administración de catálogo**.

---

## Problema

### Situación actual

Operadores de catálogo (hoy: cualquier usuario autenticado) necesitan:

1. **Crear** artistas, géneros y tracks desde modales UI.
2. **Editar** nombres y metadatos track (artista, género, explicit, duration_ms).
3. **Eliminar** entidades con confirmación modal UI.
4. **Recibir** validación nombre vacío y errores API en formularios.
5. **Persistir** cambios en `dim_artista`, dim género, `dim_track` vía API.

Riesgos sin especificación formal:

- CRUD comparte pantalla con **003** sin frontera CU/FR auditables.
- Mutaciones warehouse sin auth backend (contraste `playlists.py` con `require_user_id`).
- Interpretación errónea de “steward role” no implementado.
- Inventar auditoría o RBAC inexistentes.

### Problema de negocio

**Voxmetriks no puede gobernar mantenimiento de catálogo** si las mutaciones warehouse — expuestas en UI de consumo — carecen de reglas empresariales, trazabilidad OE→HU y delimitación explícita frente a descubrimiento (**003**), con deuda P11 documentada honestamente.

---

## Objetivo

Gobernar la **capacidad operativa de Catalog Steward (administración catálogo)**:

1. Documentar APIs POST/PUT/DELETE artists, genres, tracks.
2. Documentar modales y formularios CRUD en `/artists`, `/genres`, `/tracks`.
3. Delimitar frontera **003 consumo** vs **010 administración** en misma superficie UI.
4. Documentar validaciones implementadas (nombre vacío) y estados error modal.
5. Documentar deuda: sin rol steward, sin auth backend, sin auditoría ctl.
6. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU→FR→CA completa.

**Resultado esperado:** trazabilidad auditable de mutaciones catálogo sin inventar governance no presente en código.

---

## Alcance (Scope)

### In Scope (evidencia implementada)

- POST/PUT/DELETE API para artists, genres, tracks.
- Modales create/edit/delete en tres componentes streaming.
- Formulario artista/género: `nombre_*`.
- Formulario track: `nombre_track`, selects artista/género, `explicit`, `duration_ms`.
- Validación cliente nombre vacío; validación servidor 400 en create artists/genres/tracks.
- Confirmación delete en modal UI.
- Refresh listas tras mutación exitosa.
- Respuestas 404 en update/delete entidad inexistente; `DeleteResponse`.

### In Scope parcial (deuda documentada)

- **Governance steward:** cualquier usuario autenticado puede mutar (no `stewardGuard`).
- **Auth backend:** mutaciones sin `require_user_id` (P11).
- **Auditoría:** sin registro `ctl_auditoria` en routes CRUD.

### Out of Scope

Ver sección **Out of Scope** al final.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma que unifica experiencia musical con analítica de datos gobernada |
| **OT-09** | Objetivo Táctico | Habilitar gobierno operativo del catálogo warehouse (stewardship) |
| **OO-16** | Objetivo Operativo | Operar administración CRUD de artistas, géneros y tracks en catálogo |
| **M-16A** | Meta | 100 % creates con nombre vacío rechazados en UI antes de POST |
| **M-16B** | Meta | 100 % POST create exitosos retornan HTTP 201 con entidad creada |
| **M-16C** | Meta | 100 % DELETE/PUT entidad inexistente retornan HTTP 404 |
| **M-16D** | Meta | Documentado: mutaciones accesibles sin auth backend en implementación actual (deuda P11) |
| **DEP-06** | Departamento | **Catálogo y Contenido** |
| **PKG-02** | Paquete | `streaming` (frontend `packages/streaming/`; backend `packages/streaming/routes/` y `services/`) |

---

## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) — filas 010 pendientes integración post-ratificación.

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-CS01 | US-CS01 | FR-CS01 | CA-001 |
| CU-CS01 | US-CS01 | FR-CS16 | CA-001 |
| CU-CS01 | US-CS01 | FR-CS19 | CA-001 |
| CU-CS02 | US-CS01 | FR-CS02 | CA-002 |
| CU-CS02 | US-CS01 | FR-CS16 | CA-002 |
| CU-CS03 | US-CS01 | FR-CS03 | CA-003 |
| CU-CS03 | US-CS01 | FR-CS14 | CA-003 |
| CU-CS04 | US-CS02 | FR-CS04 | CA-004 |
| CU-CS04 | US-CS02 | FR-CS17 | CA-004 |
| CU-CS05 | US-CS02 | FR-CS05 | CA-005 |
| CU-CS06 | US-CS02 | FR-CS06 | CA-006 |
| CU-CS07 | US-CS03 | FR-CS07 | CA-007 |
| CU-CS07 | US-CS03 | FR-CS18 | CA-007 |
| CU-CS08 | US-CS03 | FR-CS08 | CA-008 |
| CU-CS09 | US-CS03 | FR-CS09 | CA-009 |
| CU-CS01 | US-CS04 | FR-CS20 | CA-010 |
| CU-CS01 | US-CS04 | FR-CS21 | CA-010 |
| CU-CS01 | US-CS04 | FR-CS22 | CA-010 |
| CU-CS03 | US-CS04 | FR-CS23 | CA-003 |
| CU-CS01 | US-CS05 | FR-CS15 | CA-011 |
| CU-CS01 | US-CS05 | FR-CS10 | CA-012 |

### Matriz de trazabilidad operativa (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS01 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS01 | US-CS01 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS04 | US-CS02 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS04 | US-CS02 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS07 | US-CS03 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS07 | US-CS03 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16C | DEP-06 | PKG-02 | CU-CS02 | US-CS01 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16C | DEP-06 | PKG-02 | CU-CS03 | US-CS01 | 010 | Implementado |
| OE-01 | OT-09 | OO-16 | M-16D | DEP-06 | PKG-02 | CU-CS01 | US-CS05 | 010 | Parcial |

---

## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Autenticado** | Cualquier usuario con sesión válida; **de facto** operador steward hoy | CRUD catálogo vía modales |
| **Operador de Catálogo** | Rol de negocio objetivo (Constitución P11); **no** implementado como guard dedicado | Mantener dim_* coherentes |
| **Sistema Voxmetriks** | Persiste mutaciones vía `get_write_conn` | Validar inputs; responder 201/404 |
| **Capa Warehouse DuckDB** | `dim_artista`, `dim_genero`, `dim_track` | Target mutaciones |

---

## Casos de Uso

### CU-CS01: Crear artista

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS01 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Sesión válida; en `/artists` |
| **Flujo principal** | 1. Usuario pulsa crear → 2. Modal solicita `nombre_artista` → 3. UI valida no vacío → 4. POST `/api/v1/artists` → 5. API inserta `dim_artista` → 6. UI cierra modal y refresca lista y top artists |
| **Postcondición** | Artista creado en warehouse |
| **Flujo alternativo** | 3a. Nombre vacío → error cliente sin POST |
| **Flujo alternativo** | 4a. API 400 → formError con detail |
| **Reglas de negocio** | RB-CS04, RB-CS06, RB-CS10 |

### CU-CS02: Editar artista

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS02 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Artista existente en lista |
| **Flujo principal** | 1. Usuario pulsa editar fila → 2. Modal precarga nombre → 3. PUT `/api/v1/artists/{id}` → 4. UI refresca lista |
| **Postcondición** | Nombre actualizado |
| **Flujo alternativo** | 3a. ID inexistente → 404 |
| **Reglas de negocio** | RB-CS04, RB-CS06 |

### CU-CS03: Eliminar artista

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS03 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Artista existente |
| **Flujo principal** | 1. Usuario pulsa eliminar → 2. Modal confirmación → 3. DELETE `/api/v1/artists/{id}` → 4. UI refresca lista |
| **Postcondición** | Fila eliminada de `dim_artista` |
| **Flujo alternativo** | 3a. 404 si no existe |
| **Reglas de negocio** | RB-CS05, RB-CS06 |

### CU-CS04: Crear género

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS04 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | Sesión; en `/genres` |
| **Flujo principal** | 1. Crear modal → 2. POST `/api/v1/genres` con `nombre_genero` → 3. Refresca lista stats |
| **Postcondición** | Género en dim género |
| **Nota** | Lista UI cargada vía `GET /genres/stats` (contexto **003**); mutación **010** |
| **Reglas de negocio** | RB-CS04, RB-CS07 |

### CU-CS05: Editar género

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS05 |
| **Actor principal** | Usuario Autenticado |
| **Flujo principal** | 1. Editar desde fila → 2. PUT `/api/v1/genres/{id}` → 3. Refresca |
| **Reglas de negocio** | RB-CS04, RB-CS07 |

### CU-CS06: Eliminar género

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS06 |
| **Actor principal** | Usuario Autenticado |
| **Flujo principal** | 1. Confirmación modal → 2. DELETE `/api/v1/genres/{id}` → 3. Refresca |
| **Reglas de negocio** | RB-CS05, RB-CS07 |

### CU-CS07: Crear track

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS07 |
| **Actor principal** | Usuario Autenticado |
| **Precondición** | En `/tracks`; listas artistas/géneros cargadas para selects |
| **Flujo principal** | 1. Modal create → 2. Usuario completa nombre, artista, género, explicit, duration_ms → 3. POST `/api/v1/tracks` → 4. Refresca tracks |
| **Postcondición** | Track en `dim_track` |
| **Reglas de negocio** | RB-CS04, RB-CS08 |

### CU-CS08: Editar track

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS08 |
| **Actor principal** | Usuario Autenticado |
| **Flujo principal** | 1. Modal edit precargado → 2. PUT `/api/v1/tracks/{id}` → 3. Refresca |
| **Reglas de negocio** | RB-CS08 |

### CU-CS09: Eliminar track

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-CS09 |
| **Actor principal** | Usuario Autenticado |
| **Flujo principal** | 1. Modal delete confirm → 2. DELETE `/api/v1/tracks/{id}` → 3. Refresca |
| **Reglas de negocio** | RB-CS05, RB-CS08 |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-CS01 — Administrar artistas (Priority: P1)

Como **Usuario Autenticado**, quiero **crear, editar y eliminar artistas desde modales en `/artists`**, para **mantener el catálogo de artistas**.

**Why this priority**: Entidad base catálogo; CU-CS01–03; OO-16.

**Independent Test**: Crear artista válido → 201; editar nombre; eliminar con confirmación; lista refresca.

**Acceptance Scenarios**:

1. **Given** usuario en `/artists`, **When** crea artista con nombre válido, **Then** POST 201 y artista en lista (FR-CS01, FR-CS16).
2. **Given** nombre vacío, **When** intenta guardar, **Then** error cliente sin POST (FR-CS19, M-16A).
3. **Given** artista existente, **When** edita y guarda, **Then** PUT 200 (FR-CS02).
4. **Given** artista existente, **When** confirma eliminar, **Then** DELETE y `{deleted:true}` (FR-CS03, FR-CS14).

**Maps to**: CU-CS01–CU-CS03 | FR-CS01–FR-CS03, FR-CS16, FR-CS19 | M-16A, M-16B

*Delimitación:* listado/búsqueda/paginación/top artists → **003**.

---

### User Story US-CS02 — Administrar géneros (Priority: P1)

Como **Usuario Autenticado**, quiero **CRUD géneros en `/genres`**, para **mantener taxonomía musical**.

**Independent Test**: CRUD género vía modales; lista stats refresca tras mutación.

**Acceptance Scenarios**:

1. **Given** modal create, **When** POST genre válido, **Then** 201 (FR-CS04, FR-CS17).
2. **Given** género en grid, **When** edit/delete, **Then** PUT/DELETE por `id_genero` (FR-CS05, FR-CS06).

**Maps to**: CU-CS04–CU-CS06 | FR-CS04–FR-CS06, FR-CS17 | M-16B

*Delimitación:* visualización stats/popularidad grid → **003**; filtro client-side búsqueda → **003**.

---

### User Story US-CS03 — Administrar tracks (Priority: P1)

Como **Usuario Autenticado**, quiero **CRUD tracks con metadatos en `/tracks`**, para **mantener catálogo canciones**.

**Independent Test**: Create track con artista/género opcionales; edit explicit/duration; delete confirm.

**Acceptance Scenarios**:

1. **Given** modal create, **When** POST con nombre y campos opcionales, **Then** 201 (FR-CS07, FR-CS18).
2. **Given** track existente, **When** edit artista/género/explicit/duration, **Then** PUT persiste (FR-CS08).
3. **Given** delete confirm, **When** DELETE, **Then** track removido lista (FR-CS09, FR-CS23).

**Maps to**: CU-CS07–CU-CS09 | FR-CS07–FR-CS09, FR-CS18, FR-CS23 | M-16B

*Delimitación:* track-row play/reproducción → **004**; listado/search tracks → **003**.

---

### User Story US-CS04 — Validación y feedback modal (Priority: P1)

Como **Usuario Autenticado**, quiero **validación de formularios y mensajes de error claros**, para **evitar mutaciones inválidas**.

**Acceptance Scenarios**:

1. **Given** nombre vacío en cualquier modal, **When** guardar, **Then** `formError` cliente (FR-CS19).
2. **Given** API error 400/404, **When** submit, **Then** `formError` muestra `detail` API (FR-CS20).
3. **Given** submit en curso, **When** `formSaving=true`, **Then** botones deshabilitados (FR-CS21).
4. **Given** mutación exitosa, **When** respuesta OK, **Then** modal cierra y lista recarga (FR-CS22).

**Maps to**: CU-CS01–CU-CS09 (transversal) | FR-CS19–FR-CS22 | M-16A

---

### User Story US-CS05 — Estado actual de acceso (Priority: P2)

Como **Sistema Voxmetriks**, debo **documentar que CRUD catálogo no exige rol steward ni auth backend hoy**, para **reflejar deuda P11 sin inventar governance**.

**Acceptance Scenarios**:

1. **Given** usuario autenticado estándar (no engineer), **When** accede modales CRUD, **Then** operación permitida (RB-CS02 — estado actual).
2. **Given** cliente API directo, **When** POST/PUT/DELETE sin token, **Then** mutación procesada si endpoint alcanzable (RB-CS03, M-16D).

**Maps to**: CU-CS01 | FR-CS15 | M-16D

---

### Edge Cases

- **Delete artista referenciado por tracks**: API ejecuta DELETE; integridad referencial avanzada no implementada en código.
- **Track update sin cambiar nombre**: PUT acepta campos opcionales (`TrackUpdate`); sin validación empty name en PUT route.
- **Género edit desde stats row**: usa `id_genero` de `GeneroPopularidad`.
- **Artists create refresca top artists**: `loadTopArtists()` post-mutación.
- **Tracks modal selects**: artistas/géneros cargados limit 200 al init.
- **Concurrent modal**: `formSaving` previene doble submit.
- **Backdrop click**: cierra modal sin guardar.

---

## Requirements *(mandatory)*

### Functional Requirements — API Artists

- **FR-CS01**: System MUST expose `POST /api/v1/artists` accepting `ArtistaCreate` (`nombre_artista`); MUST return 201 and created `Artista`; MUST reject empty name with HTTP 400.
- **FR-CS02**: System MUST expose `PUT /api/v1/artists/{artist_id}` accepting `ArtistaUpdate`; MUST return updated `Artista` or HTTP 404 if not found; MUST reject empty name with HTTP 400.
- **FR-CS03**: System MUST expose `DELETE /api/v1/artists/{artist_id}` returning `DeleteResponse` `{deleted: true, id}` or HTTP 404.

### Functional Requirements — API Genres

- **FR-CS04**: System MUST expose `POST /api/v1/genres` accepting `GeneroCreate`; MUST return 201; MUST reject empty `nombre_genero` with HTTP 400.
- **FR-CS05**: System MUST expose `PUT /api/v1/genres/{genre_id}` accepting `GeneroUpdate`; MUST return updated `Genero` or HTTP 404; MUST reject empty name with HTTP 400.
- **FR-CS06**: System MUST expose `DELETE /api/v1/genres/{genre_id}` returning `DeleteResponse` or HTTP 404.

### Functional Requirements — API Tracks

- **FR-CS07**: System MUST expose `POST /api/v1/tracks` accepting `TrackCreate` fields: `nombre_track` (required), optional `spotify_track_id`, `id_artista`, `id_album`, `id_genero`, `explicit`, `duration_ms`; MUST return 201; MUST reject empty `nombre_track` with HTTP 400.
- **FR-CS08**: System MUST expose `PUT /api/v1/tracks/{track_id}` accepting `TrackUpdate` optional fields; MUST return updated `Track` or HTTP 404.
- **FR-CS09**: System MUST expose `DELETE /api/v1/tracks/{track_id}` returning `DeleteResponse` or HTTP 404.

### Functional Requirements — API Transversal

- **FR-CS10**: POST create routes for artists, genres, tracks MUST validate non-empty stripped name server-side before write.
- **FR-CS14**: DELETE routes MUST return `DeleteResponse` with `deleted: bool` and `id: int` on success.
- **FR-CS15**: All POST/PUT/DELETE catalog routes MUST use `Depends(get_write_conn)` for warehouse mutations.

### Functional Requirements — UI Artists (`/artists`)

- **FR-CS16**: UI MUST provide create/edit/delete modals for artists with single field `nombre_artista`; MUST expose row actions edit/delete and header create button.

### Functional Requirements — UI Genres (`/genres`)

- **FR-CS17**: UI MUST provide create/edit/delete modals for genres with field `nombre_genero`.

### Functional Requirements — UI Tracks (`/tracks`)

- **FR-CS18**: UI track modals MUST include fields: `nombre_track` (required), select `id_artista`, select `id_genero`, checkbox `explicit`, number `duration_ms`; MUST load artist/genre options from GET list endpoints (limit 200) for selects.

### Functional Requirements — UI Transversal

- **FR-CS19**: UI MUST validate trimmed name non-empty client-side before POST/PUT for all three entities; MUST set localized `formError` on failure.
- **FR-CS20**: UI MUST display API error `detail` in modal `formError` on failed mutation.
- **FR-CS21**: UI MUST set `formSaving` during API call and disable primary action buttons while saving.
- **FR-CS22**: UI MUST close modal and reload entity list (and top artists for artists) on successful mutation.
- **FR-CS23**: UI delete modals MUST require explicit confirm action before DELETE API call.

### Functional Requirements — Delimitación 003

- **FR-CS24**: Spec **010** MUST NOT define GET list/search/stats/browse FRs; those remain owned by spec **003**. Steward FRs apply only to POST/PUT/DELETE and associated modals on shared routes.

---

## Non-Functional Requirements

- **NFR-CS01 (Performance)**: Catalog mutation API calls SHOULD complete ≤ 3 s p95 en entorno local demo.
- **NFR-CS02 (UX)**: Modals MUST show spinner/disabled state during `formSaving`.
- **NFR-CS03 (Reliability)**: Failed mutations MUST leave modal open with error message, not crash SPA.
- **NFR-CS04 (Data integrity — P6)**: Mutations MUST target warehouse dimension tables via write connection only.
- **NFR-CS05 (Security — current state)**: Catalog mutation APIs documented as **without server-side authentication** in current implementation (P11 deuda; RB-CS03).
- **NFR-CS06 (Auditability — current state)**: Mutations MUST NOT write to `ctl_auditoria` in current implementation (RB-CS09).
- **NFR-CS07 (Maintainability)**: Feature MUST document CU→FR→CA matrix and 003/010 boundary in this spec.
- **NFR-CS08 (Consistency)**: Delete confirmation UX MUST be consistent across artists, genres, tracks (modal + warn text).
- **NFR-CS09 (Validation)**: Client and server MUST both reject empty names on create paths documented in FR-CS10.
- **NFR-CS10 (Traceability)**: Steward operations MUST map to OO-16 without claiming steward role enforcement not in code.

---

## Reglas de Negocio

- **RB-CS01**: Catalog steward mutations MUST persist to warehouse tables `dim_artista`, dim género table, `dim_track` respectively.
- **RB-CS02**: CRUD modals on `/artists`, `/genres`, `/tracks` are available to **any authenticated user** in current implementation — **no** `stewardGuard` exists.
- **RB-CS03**: POST/PUT/DELETE catalog endpoints have **no** `require_user_id` or role check in current code (P11 documented debt).
- **RB-CS04**: `nombre_artista`, `nombre_genero`, `nombre_track` MUST NOT be empty on create (client + server where implemented).
- **RB-CS05**: DELETE MUST require user confirmation via UI modal before API call; API itself has no dual confirmation.
- **RB-CS06**: Spec **003** owns browse/search/read UX on same pages; **010** owns write modals and mutation APIs only.
- **RB-CS07**: Genres steward UI operates on rows from `GET /genres/stats` display; mutations use standard genre CRUD API by `id_genero`.
- **RB-CS08**: Track steward form MUST support optional artist/genre FK selects and optional explicit/duration fields as implemented — not extended fields absent from forms.
- **RB-CS09**: Catalog CRUD routes MUST NOT invoke audit logging to `ctl_auditoria` in current implementation.
- **RB-CS10**: Successful steward mutation MUST trigger list refresh in UI (`loadArtists`, `loadGenres`, `loadTracks` as applicable).
- **RB-CS11**: New entity IDs MUST be assigned server-side as `MAX(id)+1` per dimension table (evidencia services).

---

## Criterios de Aceptación Globales

1. **CA-001**: POST artist válido crea fila dim_artista y refresca UI (CU-CS01).
2. **CA-002**: PUT artist actualiza nombre existente (CU-CS02).
3. **CA-003**: DELETE artist con confirmación modal elimina registro (CU-CS03).
4. **CA-004**: POST genre válido crea género (CU-CS04).
5. **CA-005**: PUT genre actualiza nombre (CU-CS05).
6. **CA-006**: DELETE genre con confirmación (CU-CS06).
7. **CA-007**: POST track con campos formulario implementados (CU-CS07).
8. **CA-008**: PUT track actualiza metadatos (CU-CS08).
9. **CA-009**: DELETE track con confirmación (CU-CS09).
10. **CA-010**: Errores API y validación cliente visibles en modal (US-CS04).
11. **CA-011**: Mutaciones usan write conn documentado (FR-CS15).
12. **CA-012**: Nombre vacío rechazado en create server-side artists/genres/tracks (FR-CS10, M-16A).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-CS01**: 100% intentos create con nombre vacío bloqueados en UI antes de POST (M-16A).
- **SC-CS02**: 100% POST create válidos en prueba integración retornan HTTP 201 (M-16B).
- **SC-CS03**: 100% PUT/DELETE sobre ID inexistente retornan HTTP 404 (M-16C).
- **SC-CS04**: 100% DELETE exitosos retornan `DeleteResponse.deleted=true` (FR-CS14).
- **SC-CS05**: 0 endpoints steward inventados fuera de POST/PUT/DELETE documentados (evidencia audit).
- **SC-CS06**: Documentación 003/010 boundary presente y auditable en spec (RB-CS06).
- **SC-CS07**: Deuda P11 auth backend documentada sin requisito ficticio de steward role (M-16D, NFR-CS05).

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-CS01 | Duplicidad CU/FR con spec 003 | Alta | Alto | Tabla delimitación; FR-CS24; RB-CS06 |
| R-CS02 | CRUD sin auth backend (P11) | Alta | Alto | RB-CS03, NFR-CS05; Out of Scope RBAC |
| R-CS03 | Usuario asume rol steward implementado | Alta | Medio | RB-CS02, US-CS05 |
| R-CS04 | Delete rompe referencias FK | Media | Medio | Documentar; Out of Scope integridad avanzada |
| R-CS05 | Inventar auditoría ctl | Media | Alto | RB-CS09, Out of Scope |
| R-CS06 | Mutaciones afectan KPIs 007/008 | Media | Medio | Dependencia downstream documentada |
| R-CS07 | Genres CRUD desde vista stats confunde | Media | Bajo | RB-CS07 |
| R-CS08 | Track PUT sin validación empty name | Baja | Bajo | Documentar estado actual edge case |
| R-CS09 | Cualquier auth user borra catálogo | Alta | Alto | Deuda P11; no inventar mitigación no coded |
| R-CS10 | Spec 003 Out of Scope desalineado con UI | Media | Medio | Esta spec formaliza steward explícitamente |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| `001-user-identity-access` | Hard | Sesión, authGuard en layout |
| `003-catalog-discovery` | Hard | Mismas rutas UI; 003 owns read paths |
| Warehouse DuckDB dims | Hard | dim_artista, dim_genero, dim_track |
| `ArtistsService`, `GenresService`, `TracksService` | Hard | Métodos CRUD FE |
| `get_write_conn` | Hard | Conexión escritura warehouse |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | P6 warehouse writes, P11 deuda auth, §3.1 catálogo CRUD |
| `SPEC-008-011-EVIDENCE-AUDIT.md` | Evidencia única alcance 010 |
| `003-catalog-discovery/spec.md` | Out of Scope steward; delimitación consumo |

### Specs downstream (010 impacta)

| Spec | Relación |
|------|----------|
| `007-operational-analytics-dashboards` | KPIs catálogo reflejan mutaciones dim_* |
| `008-pipeline-monitoring` | Synthetic expande dim_track independiente steward |
| `004-listening-experience` | Play tracks listados; no mutación |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§3.1 In Scope** | Catálogo CRUD incluido; steward documentado |
| **§5 P2 Package-by-Domain** | PKG-02 streaming |
| **§5 P6 Warehouse vs App** | Mutaciones dim_* warehouse |
| **§5 P11 Security mutations** | RB-CS03 deuda auth; target steward futuro |
| **§12 Trazabilidad** | OT-09, OO-16, M-16A–D |
| **§14 Nomenclatura** | Branch `010-catalog-steward` |

---

## Out of Scope

- Rol `steward` / `stewardGuard` dedicado (no implementado).
- Autenticación/autorización backend en mutaciones catálogo (no implementado).
- Registro auditoría `ctl_auditoria` en CRUD routes.
- Pantalla steward separada de `/artists`, `/genres`, `/tracks`.
- Confirmación dual DELETE en API (solo modal UI).
- Validaciones integridad referencial avanzadas (cascade rules).
- Bulk import/export catálogo.
- CRUD álbumes (`dim_album`) — no expuesto en UI steward actual.
- Browse/search/list/play FRs — spec **003** / **004**.
- Pipeline synthetic (**008**).
- Explorer warehouse (**009**).

---

## Assumptions

- Usuario debe estar autenticado (`authGuard`) para alcanzar modales CRUD.
- Warehouse write path disponible vía `get_write_conn`.
- Listas artista/género para track selects cargables vía GET existentes (**003** endpoints).
- Mensajes error API FastAPI exponen campo `detail` string o array.
- Idioma UI modales español en implementación actual (labels hardcoded en templates).
- Operador conoce impacto de DELETE en datos demo; entorno no producción crítica.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — evidencia `SPEC-008-011-EVIDENCE-AUDIT.md`  
**Next Step**: `/speckit-checklist` → `/speckit-plan` — Constitution Check P6, P11; delimitación enmienda referencial 003 recomendada post-ratificación 010.
