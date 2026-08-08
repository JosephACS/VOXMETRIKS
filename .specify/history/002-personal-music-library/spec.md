> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Biblioteca Personal de Música

**Feature Branch**: `002-personal-music-library`  
**Feature Directory**: `specs/002-personal-music-library/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de biblioteca personal: gestión de playlists y favoritos por usuario autenticado, con aislamiento de datos y trazabilidad empresarial.

**Prerrequisito:** `specs/001-user-identity-access/` — autenticación, sesión y control de acceso MUST estar operativos.

**Delimitación vs 001:** Esta spec NO redefine registro, login, logout ni emisión de tokens. Asume identidad válida según spec 001 y define únicamente operaciones sobre **biblioteca personal** (playlists, favoritos).

---

## Contexto Empresarial

Voxmetriks posiciona la **personalización musical** como pilar estratégico (Constitución §2, OE-01). La meta **M-01** establece que el 100% de operaciones sobre biblioteca personal MUST ejecutarse solo con identidad autenticada válida — requisito de acceso cubierto por spec **001**. Esta spec **002** define **qué** puede hacer el usuario autenticado con su biblioteca y **cómo** el sistema garantiza aislamiento, persistencia y reglas de negocio.

La auditoría confirmó implementación funcional de 7 endpoints playlists y 3 endpoints favorites, tablas `app_playlist`, `app_playlist_track`, `app_favorite`, e integración UI (`/playlists`, `/liked`, componentes `favorite-btn`, `add-to-playlist-btn`). Sin embargo, **no existía gobernanza SDD** ni criterios de aceptación empresariales unificados para este dominio.

La biblioteca personal es el **primer módulo de valor post-identidad**: materializa el retorno de inversión en registro/login para el usuario final.

---

## Problema

### Situación actual

Usuarios autenticados necesitan:

1. **Organizar** música en playlists propias persistentes.
2. **Marcar** tracks favoritos en una biblioteca "Liked Songs" unificada.
3. **Confiar** en que ningún otro usuario ve o modifica su biblioteca.
4. **Operar** desde catálogo, detalle de track, reproductor y pantallas dedicadas.

Riesgos sin especificación formal:

- Ambigüedad en scoping user_id (playlists de otro usuario).
- Duplicados de tracks en playlist sin regla clara.
- Idempotencia de favoritos no documentada.
- Stats de perfil (spec 001 CU-03) dependen de conteos de este dominio sin contrato explícito.

### Problema de negocio

**Los usuarios no pueden declarar Voxmetriks como su biblioteca musical personal** si las reglas de playlists y favoritos no están definidas, medibles y auditables como capacidad operativa empresarial.

---

## Objetivo

Gobernar la **capacidad operativa de Biblioteca Personal de Música** en Voxmetriks:

1. CRUD de playlists scoped por usuario autenticado.
2. Gestión de tracks dentro de playlists (añadir, quitar).
3. Gestión de favoritos (listar, añadir, quitar) scoped por usuario.
4. Persistencia en capa aplicación (`app_*`), separada del warehouse ELT.
5. Integración UX desde pantallas dedicadas y acciones contextuales (botones favorito / añadir a playlist).
6. Contribución a estadísticas de perfil (`favorites_count`, `playlists_count`) referenciadas en spec 001.

**Resultado esperado:** usuario autenticado opera biblioteca personal completa con aislamiento garantizado y trazabilidad OE→Impl.

---

## Trazabilidad Empresarial

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma referencia: experiencia musical personalizada + analítica gobernada |
| **OT-02** | Objetivo Táctico | Habilitar dominio streaming de biblioteca personal persistente por usuario |
| **OO-02** | Objetivo Operativo | Operar playlists personales CRUD y gestión de tracks en playlist |
| **OO-03** | Objetivo Operativo | Operar biblioteca de favoritos personales |
| **M-1A** | Meta | 100% operaciones playlists requieren identidad válida (hereda M-01 spec 001) |
| **M-1B** | Meta | 100% operaciones favoritos requieren identidad válida (hereda M-01 spec 001) |
| **M-1C** | Meta | 0 accesos cross-user a playlists/favoritos ajenos en pruebas de aislamiento |
| **M-1D** | Meta | Usuario crea playlist y añade primer track en ≤ 60 segundos (UX operativa) |
| **DEP-02** | Departamento | **Producto Streaming** |
| **PKG-02** | Paquete | `streaming` (backend routes/services playlists+favorites; frontend playlists, liked, shared buttons) |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../README.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-P01 | US-P01 | FR-P01 | CA-001 |
| CU-P02 | US-P01 | FR-P02 | CA-001 |
| CU-P03 | US-P01 | FR-P03 | CA-001 |
| CU-P04 | US-P01 | FR-P04 | CA-001 |
| CU-P05 | US-P01 | FR-P05 | CA-001 |
| CU-P06 | US-P02 | FR-P06 | CA-002 |
| CU-P07 | US-P02 | FR-P07 | CA-002 |
| CU-P01 | US-P01 | FR-P08 | CA-006 |
| CU-P02 | US-P01 | FR-P09 | CA-004 |
| CU-P04 | US-P01 | FR-P10 | CA-004 |
| CU-P06 | US-P02 | FR-P11 | CA-005 |
| CU-P03 | US-P01 | FR-P12 | CA-001 |
| CU-P07 | US-P03 | FR-P13 | CA-002 |
| CU-F01 | US-F01 | FR-F01 | CA-003 |
| CU-F02 | US-F01 | FR-F02 | CA-003 |
| CU-F03 | US-F01 | FR-F03 | CA-003 |
| CU-F04 | US-F01 | FR-F04 | CA-005 |
| CU-F04 | US-F01 | FR-F05 | CA-005 |
| CU-F01 | US-F01 | FR-F06 | CA-003 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P01 | US-P01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P02 | US-P01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P03 | US-P01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P04 | US-P01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P05 | US-P01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P06 | US-P02 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P07 | US-P02 | 002 | Pendiente |
| OE-01 | OT-02 | OO-02 | M-1D | DEP-02 | PKG-02 | CU-P07 | US-P03 | 002 | Pendiente |
| OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F01 | US-F01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F02 | US-F01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F03 | US-F01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F04 | US-F01 | 002 | Pendiente |
| OE-01 | OT-02 | OO-03 | M-1C | DEP-02 | PKG-02 | CU-F01 | US-F01 | 002 | Pendiente |
## Actores

| Actor | Descripción |
|-------|-------------|
| **Usuario Registrado Autenticado** | Opera biblioteca personal; subject de scoping user_id |
| **Sistema Voxmetriks** | Persiste, valida, aísla datos biblioteca |
| **Usuario Visitante** | Sin acceso — redirigido por spec 001 CU-06 |


*Nota:* Perfil API (001) consume stats de este dominio como actor indirecto.

---

## Casos de Uso

### CU-P01: Listar playlists propias

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida según spec 001 |
| **Flujo principal** | 1. Usuario solicita listado → 2. Sistema filtra por user_id → 3. Sistema retorna solo playlists propias |
| **Postcondición** | Lista playlists del usuario visible en UI |
| **Flujo alternativo** | 2a. Sin sesión → 401 / redirect login (001) |
| **Reglas de negocio** | RB-P01, RB-P03 |

### CU-P02: Crear playlist

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida; nombre no vacío |
| **Flujo principal** | 1. Usuario ingresa nombre y descripción opcional → 2. Sistema valida → 3. Sistema persiste playlist con user_id |
| **Postcondición** | Playlist creada y visible en listado |
| **Flujo alternativo** | 2a. Nombre vacío → error validación (RB-P02) |
| **Reglas de negocio** | RB-P01, RB-P02 |

### CU-P03: Ver detalle playlist con tracks

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Playlist pertenece al usuario |
| **Flujo principal** | 1. Usuario solicita detalle → 2. Sistema verifica ownership → 3. Sistema retorna metadata y tracks ordenados |
| **Postcondición** | Detalle playlist mostrado |
| **Flujo alternativo** | 2a. Playlist ajena o inexistente → 404 sin filtrar datos (RB-P03, FR-P12) |
| **Reglas de negocio** | RB-P03, RB-P04 |

### CU-P04: Editar playlist

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Ownership de playlist |
| **Flujo principal** | 1. Usuario modifica nombre/descripción → 2. Sistema valida → 3. Sistema persiste cambios |
| **Postcondición** | Metadatos actualizados |
| **Flujo alternativo** | 2a. Nombre inválido → error |
| **Reglas de negocio** | RB-P02, RB-P03 |

### CU-P05: Eliminar playlist

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P05 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Ownership de playlist |
| **Flujo principal** | 1. Usuario confirma eliminación → 2. Sistema elimina playlist y junction tracks |
| **Postcondición** | Playlist eliminada |
| **Flujo alternativo** | 2a. No owner → 404 |
| **Reglas de negocio** | RB-P03, RB-P05 |

### CU-P06: Añadir track a playlist

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P06 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Playlist propia; track existe en catálogo (003) |
| **Flujo principal** | 1. Usuario selecciona track → 2. Sistema valida → 3. Sistema añade junction si no duplicado |
| **Postcondición** | Track visible en detalle playlist |
| **Flujo alternativo** | 2a. Track inexistente → 404; 2b. Duplicado → ignorar o rechazar (RB-P06) |
| **Reglas de negocio** | RB-P04, RB-P06 |

### CU-P07: Quitar track de playlist

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-P07 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Ownership; track en playlist |
| **Flujo principal** | 1. Usuario quita track → 2. Sistema elimina junction |
| **Postcondición** | Track removido de playlist |
| **Flujo alternativo** | 2a. Track no en playlist → idempotente sin error |
| **Reglas de negocio** | RB-P03 |

### CU-F01: Listar favoritos

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-F01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario abre biblioteca favoritos → 2. Sistema retorna tracks favoritos del user_id |
| **Postcondición** | Lista favoritos visible |
| **Flujo alternativo** | 2a. Sin favoritos → empty state |
| **Reglas de negocio** | RB-F01, RB-F04 |

### CU-F02: Añadir favorito

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-F02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Track válido en catálogo |
| **Flujo principal** | 1. Usuario marca favorito → 2. Sistema persiste par user-track único |
| **Postcondición** | Track en favoritos |
| **Flujo alternativo** | 2a. Ya favorito → idempotente (RB-F03) |
| **Reglas de negocio** | RB-F01, RB-F02 |

### CU-F03: Quitar favorito

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-F03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario desmarca favorito → 2. Sistema elimina relación |
| **Postcondición** | Track removido de favoritos |
| **Flujo alternativo** | 2a. No existía → idempotente (RB-F03) |
| **Reglas de negocio** | RB-F03 |

### CU-F04: Toggle favorito desde UI contextual

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-F04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Usuario en contexto track (catálogo, detalle, recomendaciones) |
| **Flujo principal** | 1. Usuario pulsa toggle → 2. Sistema invoca add/remove → 3. UI refleja estado |
| **Postcondición** | Estado favorito coherente UI/backend |
| **Flujo alternativo** | 2a. Sin auth → redirect 001 |
| **Reglas de negocio** | RB-F02, RB-F03 |

---


## User Scenarios & Testing *(mandatory)*

### User Story US-P01 — Crear y gestionar playlists (Priority: P1)

Como **Usuario Registrado**, quiero **crear, renombrar, describir y eliminar mis playlists**, para **organizar mi música personal**.

**Why this priority**: Core valor biblioteca personal; entregable MVP del dominio.

**Independent Test**: Crear playlist "Mi lista", editar nombre, eliminar — sin usar favoritos.

**Acceptance Scenarios**:

1. **Given** usuario autenticado en `/playlists`, **When** crea playlist con nombre válido, **Then** aparece en listado y persiste tras recarga.
2. **Given** playlist propia, **When** edita nombre/descripción, **Then** cambios persisten.
3. **Given** playlist propia, **When** elimina, **Then** desaparece del listado y tracks junction eliminados.
4. **Given** nombre vacío o solo espacios, **When** intenta crear/editar, **Then** sistema rechaza con error claro.
5. **Given** usuario A autenticado, **When** intenta acceder playlist ID de usuario B, **Then** 404 o equivalente (no revelar existencia ajena).

**Maps to**: CU-P01–P05 | FR-P01–P08

---

### User Story US-P02 — Gestionar tracks en playlist (Priority: P1)

Como **Usuario Registrado**, quiero **añadir y quitar tracks de mis playlists**, para **componer colecciones escuchables**.

**Independent Test**: Añadir 2 tracks, quitar 1, verificar detalle.

**Acceptance Scenarios**:

1. **Given** playlist propia y track válido del catálogo, **When** añade track, **Then** aparece en detalle playlist.
2. **Given** track en playlist, **When** quita track, **Then** ya no aparece en detalle.
3. **Given** track inexistente, **When** añade a playlist, **Then** error 404.
4. **Given** botón "añadir a playlist" en UI track, **When** selecciona playlist, **Then** track añadido sin navegar away.

**Maps to**: CU-P06–P07 | FR-P09–P12

---

### User Story US-F01 — Gestionar favoritos (Priority: P1)

Como **Usuario Registrado**, quiero **marcar y desmarcar tracks como favoritos**, para **acceder rápidamente a mi biblioteca Liked Songs**.

**Independent Test**: Favoritar 3 tracks, ver `/liked`, desmarcar 1.

**Acceptance Scenarios**:

1. **Given** track no favorito, **When** marca favorito, **Then** aparece en `/liked` y botón refleja estado activo.
2. **Given** track favorito, **When** desmarca, **Then** desaparece de `/liked`.
3. **Given** track ya favorito, **When** marca de nuevo, **Then** operación idempotente sin error.
4. **Given** usuario A, **When** lista favoritos, **Then** no ve favoritos de usuario B.

**Maps to**: CU-F01–F04 | FR-F01–F06

---

### User Story US-P03 — Reproducir desde biblioteca (Priority: P2)

Como **Usuario Registrado**, quiero **iniciar reproducción desde playlist o favoritos**, para **escuchar mi biblioteca** (integración con spec 004).

**Independent Test**: Play all desde detalle playlist carga cola reproductor.

**Acceptance Scenarios**:

1. **Given** playlist con tracks, **When** pulsa reproducir playlist, **Then** cola del reproductor se puebla (spec 004).
2. **Given** favoritos listados, **When** reproduce track, **Then** reproductor inicia track seleccionado.

**Maps to**: CU-P07 extensión | FR-P13 — *dependencia spec 004*

---

### Edge Cases

- Playlist vacía: MUST listarse; detalle muestra estado vacío sin error.
- Añadir mismo track dos veces a playlist: sistema MUST prevenir duplicado o ignorar silenciosamente (regla RB-P06).
- Eliminar track del catálogo warehouse: favoritos/playlist junction MUST manejar gracefully (404 en add; orphan handling documentado en plan).
- Sesión expirada mid-operation: MUST retornar no autenticado (001).
- Usuario sin playlists: listado vacío con empty-state UX.

---

## Requirements *(mandatory)*

### Functional Requirements — Playlists

- **FR-P01**: System MUST list playlists filtered by authenticated user_id only.
- **FR-P02**: System MUST create playlist with name (required, non-blank), optional description, scoped to user_id.
- **FR-P03**: System MUST return playlist detail including ordered tracks with catalog metadata joins.
- **FR-P04**: System MUST update playlist name/description for owner only.
- **FR-P05**: System MUST delete playlist and associated track junction rows for owner only.
- **FR-P06**: System MUST add track to playlist when both exist and user owns playlist.
- **FR-P07**: System MUST remove track from playlist for owner.
- **FR-P08**: System MUST reject unauthenticated access to all playlist endpoints (delegado a 001).
- **FR-P09**: UI MUST provide dedicated `/playlists` management screen.
- **FR-P10**: UI MUST provide create/edit/delete flows with validation feedback.
- **FR-P11**: UI MUST provide add-to-playlist action from track contexts via shared component.
- **FR-P12**: System MUST return 404 when playlist not found OR not owned (no information leakage).
- **FR-P13**: UI MUST support play-all action delegating queue to music player (004).

### Functional Requirements — Favoritos

- **FR-F01**: System MUST list favorite tracks for authenticated user only.
- **FR-F02**: System MUST add favorite when track exists in catalog.
- **FR-F03**: System MUST remove favorite idempotently.
- **FR-F04**: UI MUST provide `/liked` screen listing favorites.
- **FR-F05**: UI MUST provide favorite toggle button reflecting current state with optimistic or confirmed update.
- **FR-F06**: Client MAY cache favorite state for UX responsivo; MUST reconcile with server on load.

### Non-Functional Requirements

- **NFR-01**: Playlist list MUST respond ≤ 2s p95 con ≤ 100 playlists por usuario.
- **NFR-02**: Favorite toggle MUST reflejar feedback visual ≤ 500ms (optimistic acceptable).
- **NFR-03**: 100% requests MUST include auth credential (001 interceptor).
- **NFR-04**: Data MUST persist in application layer tables, never mixed con warehouse ELT (Constitución P6).
- **NFR-05**: Operaciones MUST ser auditables via user_id en cada mutación.

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-P01** | Toda playlist MUST tener `user_id` del creador; inmutable por otros usuarios. |
| **RB-P02** | Nombre playlist MUST NOT estar vacío ni solo whitespace. |
| **RB-P03** | Solo el owner MAY modificar/eliminar playlist. |
| **RB-P04** | Track añadido MUST existir en catálogo (`dim_track` / servicio tracks). |
| **RB-P05** | Eliminación playlist MUST cascader junction `app_playlist_track`. |
| **RB-P06** | Mismo track MUST NOT duplicarse en misma playlist (una entrada por track_id). |
| **RB-F01** | Par (user_id, track_id) MUST ser único en favoritos. |
| **RB-F02** | Favorito MUST referenciar track válido del catálogo. |
| **RB-F03** | Remove favorito inexistente MUST NOT error (idempotente). |
| **RB-F04** | Conteo favoritos en perfil (001) MUST derivar de este dominio. |

### Key Entities

- **Playlist**: id, user_id, name, description, created_at, track_count (derivado).
- **PlaylistTrack** (junction): playlist_id, track_id, position/added_at.
- **Favorite**: user_id, track_id, added_at.
- **FavoriteTrack** (vista): track metadata + favorited timestamp para UI.

---

## Criterios de Aceptación Globales (Feature)

- **CA-001**: Usuario autenticado CRUD playlist completo sin acceder datos ajenos.
- **CA-002**: Añadir/quitar tracks en playlist propia funciona end-to-end.
- **CA-003**: Favoritos listar/añadir/quitar con aislamiento por usuario.
- **CA-004**: UI `/playlists` y `/liked` operativas con empty states.
- **CA-005**: Botones contextuales favorite/add-to-playlist integrados en catálogo/detalle.
- **CA-006**: Sin auth → 401 en API; redirect login en UI (001).
- **CA-007**: Stats perfil reflejan conteos correctos post-operaciones.

---

## Success Criteria *(mandatory)*

- **SC-001**: 95% usuarios crean primera playlist en ≤ 60s tras autenticación.
- **SC-002**: 100% intentos acceso playlist ajena fallan sin filtrar datos.
- **SC-003**: 0 favoritos cruzados entre usuarios en suite aislamiento.
- **SC-004**: 90% operaciones favorito completan en ≤ 2s incluyendo UI feedback.

---

## Riesgos

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-001 | Dependencia estricta spec 001 no cerrada | Plan 002 bloqueado hasta 001 plan/tasks |
| R-002 | Track eliminado del catálogo deja orphans | Plan: FK strategy o cleanup job |
| R-003 | Duplicados playlist track | RB-P06 enforcement |
| R-004 | Cache favoritos desincronizado | Reconcile on page load |

---

## Dependencias

| Dependencia | Tipo | Referencia |
|-------------|------|------------|
| Identidad y acceso | Hard | `001-user-identity-access` |
| Catálogo tracks | Hard | `003-catalog-discovery` (track must exist) |
| Reproductor | Soft | `004-listening-experience` (play from library) |
| Perfil stats | Soft | `001` CU-03 consume counts |
| Warehouse | Indirect | Catalog read only; NO writes to dim_* from library |

---

## Relación con Constitución v1.0.0

| Sección | Aplicación |
|---------|------------|
| §5 P2 Package-by-domain | Dominio `streaming` |
| §5 P6 Warehouse vs app | FR-F/NFR-04: `app_playlist*`, `app_favorite` |
| §5 P9 Contract-first | Alinear OpenAPI + api.models.ts en plan |
| §5 P11 Auth mutations | 100% endpoints auth required |
| §12 Trazabilidad | Matriz completa |
| M-01 | Materialización operativa post-001 |

---

## Out of Scope

- Playlists colaborativas / compartidas entre usuarios
- Import/export playlists externas (Spotify)
- Orden manual drag-drop tracks en playlist (mejora futura)
- Registro/login (001)
- Reproductor completo (004)

---

## Assumptions

- Un usuario MAY tener ilimitadas playlists (sin cuota v1).
- Tracks referenciados existen en catálogo poblado por ELT.
- Auth Bearer funciona según spec 001.

---

**Next Step**: `/speckit-plan` — Constitution Check contra P2, P6, P11.
