# Feature Specification: Experiencia Operativa de Escucha

**Feature Branch**: `004-listening-experience`  
**Feature Directory**: `specs/004-listening-experience/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de reproducción musical, cola de escucha y hub Home post-autenticación.

**Prerrequisitos:** `001-user-identity-access`; `003-catalog-discovery` (metadata tracks); `002-personal-music-library` (opcional play from library).

**Delimitación vs 003:** Esta spec NO define navegación catálogo — solo **reproducción, cola, controles y Home hub**.

**Delimitación Constitución:** Voxmetriks NO es streaming real — audio demo/local (§1, §23.3). Spec MUST documentar esta restricción como regla de negocio.

---

## Contexto Empresarial

La propuesta de valor de Voxmetriks incluye **experiencia de consumo tipo streaming** (Constitución §2.3). Tras autenticación (001) y descubrimiento (003), el usuario MUST poder **escuchar**, **controlar reproducción** y **retomar** desde un hub operativo (Home).

Evidencia: `MusicPlayerService`, `player-bar`, `now-playing-view`, `/dashboard` (HomeComponent) integrando stats, playlists recientes, top tracks, historial local. Audio vía `demo-audio.config.ts` — WAV demo, no CDN streaming.

Esta spec gobierna la **experiencia operativa de escucha** dentro de las restricciones producto, sin redefinir catálogo ni biblioteca personal.

---

## Problema

- Reproductor y Home existen sin criterios empresariales de cola, shuffle, repeat, persistencia volumen.
- Historial local (`HistoryService`) alimenta Home pero no está unificado con spec 005.
- Usuario espera continuidad post-login — Home MUST agregar personalización sin duplicar analytics enterprise.

**Problema de negocio:** sin experiencia de escucha gobernada, Voxmetriks permanece como "catálogo con botones" sin sensación de producto streaming operativo.

---

## Objetivo

1. Operar reproductor global persistente (play/pause, seek, volume, shuffle, repeat).
2. Gestionar cola de reproducción desde catálogo, biblioteca y Home.
3. Proveer Hub Home como centro operativo post-login con resumen personalizado.
4. Registrar escucha en historial local (integración 005).
5. Documentar explícitamente limitación audio demo (no streaming backend).

---

## Trazabilidad Empresarial

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Estratégico | Plataforma UX musical personalizada |
| **OT-04** | Táctico | Capa experiencia escucha SPA con reproductor global |
| **OO-06** | Operativo | Operar sesión de escucha con controles y cola |
| **OO-07** | Operativo | Operar hub Home post-autenticación |
| **M-6A** | Meta | Reproductor accesible desde 100% rutas shell autenticado |
| **M-6B** | Meta | Transición play→audio audible ≤ 2s (demo assets) |
| **M-7A** | Meta | Home carga contenido personalizado ≤ 3s p95 |
| **DEP-02** | Departamento | **Producto Streaming** |
| **PKG-03** | Paquete | `shared/services/music-player`, `shared/components/player-bar`, `streaming/home` |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-R01 | US-R01 | FR-R01 | CA-001 |
| CU-R01 | US-R01 | FR-R02 | CA-001 |
| CU-R01 | US-R01 | FR-R03 | CA-005 |
| CU-R01 | US-R01 | FR-R07 | CA-003 |
| CU-R01 | US-R01 | FR-R03 | CA-001 |
| CU-R02 | US-R01 | FR-R02 | CA-001 |
| CU-R03 | US-R01 | FR-R04 | CA-001 |
| CU-R04 | US-R01 | FR-R09 | CA-001 |
| CU-R05 | US-R02 | FR-R05 | CA-002 |
| CU-R06 | US-R02 | FR-R06 | CA-002 |
| CU-R07 | US-R02 | FR-R10 | CA-002 |
| CU-R01 | US-R02 | FR-R08 | CA-003 |
| CU-R08 | US-R03 | FR-R12 | CA-001 |
| CU-R01 | US-R04 | FR-R11 | CA-003 |
| CU-R01 | US-R04 | FR-R13 | CA-006 |
| CU-H01 | US-H01 | FR-H01 | CA-004 |
| CU-H01 | US-H01 | FR-H02 | CA-004 |
| CU-H02 | US-H01 | FR-H03 | CA-004 |
| CU-H03 | US-H01 | FR-H04 | CA-004 |
| CU-H04 | US-H01 | FR-H04 | CA-006 |
| CU-H03 | US-H01 | FR-H05 | CA-004 |
| CU-H02 | US-H01 | FR-H06 | CA-004 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6B | DEP-02 | PKG-03 | CU-R01 | US-R01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R02 | US-R01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R03 | US-R01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R04 | US-R01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R05 | US-R02 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R06 | US-R02 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R07 | US-R02 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R02 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R08 | US-R03 | 004 | Pendiente |
| OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R04 | 004 | Pendiente |
| OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H01 | US-H01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H02 | US-H01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H03 | US-H01 | 004 | Pendiente |
| OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H04 | US-H01 | 004 | Pendiente |


---
## Actores

| Actor | Descripción |
|-------|-------------|
| **Usuario Registrado** | Escucha, controla, navega Home |
| **Sistema Voxmetriks** | Gestiona cola, HTML5 Audio, persistencia prefs locales |


## Casos de Uso

### CU-R01: Reproducir track desde contexto

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R01 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Track seleccionado con metadata válida (003/002) |
| **Flujo principal** | 1. Usuario pulsa play → 2. Sistema resuelve demo audio URL → 3. Reproductor inicia |
| **Postcondición** | Audio en reproducción; barra activa |
| **Flujo alternativo** | 2a. Asset demo ausente → error amigable (RB-R01) |
| **Reglas de negocio** | RB-R01, RB-R02 |

### CU-R02: Pausar / reanudar

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R02 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Track cargado en reproductor |
| **Flujo principal** | 1. Usuario toggle play/pause → 2. Sistema controla HTML5 Audio |
| **Postcondición** | Estado playing/paused coherente en UI |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-R02 |

### CU-R03: Ajustar volumen

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R03 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Reproductor activo |
| **Flujo principal** | 1. Usuario ajusta volumen → 2. Sistema aplica y persiste local |
| **Postcondición** | Volumen persistido entre sesiones |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-R04 |

### CU-R04: Seek en progreso

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R04 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Duración conocida |
| **Flujo principal** | 1. Usuario arrastra progreso → 2. Sistema seek audio |
| **Postcondición** | Posición actualizada |
| **Flujo alternativo** | 2a. Duración desconocida → seek deshabilitado |
| **Reglas de negocio** | RB-R01 |

### CU-R05: Siguiente / anterior en cola

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R05 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Cola con ≥1 track |
| **Flujo principal** | 1. Usuario next/prev → 2. Sistema avanza cola |
| **Postcondición** | Track actual cambia |
| **Flujo alternativo** | 2a. Cola vacía → no-op |
| **Reglas de negocio** | RB-R03 |

### CU-R06: Activar shuffle / repeat

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R06 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Cola activa |
| **Flujo principal** | 1. Usuario toggle modo → 2. Sistema aplica algoritmo cola |
| **Postcondición** | Modo shuffle/repeat activo |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-R03 |

### CU-R07: Reproducir cola completa

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R07 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Origen playlist/favoritos/lista (002/003) |
| **Flujo principal** | 1. Usuario play all → 2. Sistema puebla cola → 3. Inicia primer track |
| **Postcondición** | Cola reproduciendo secuencialmente |
| **Flujo alternativo** | 2a. Lista vacía → mensaje |
| **Reglas de negocio** | RB-R01 |

### CU-R08: Ver now-playing expandido

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-R08 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Track en reproducción o pausa |
| **Flujo principal** | 1. Usuario expande player → 2. UI modal/sheet con controles ampliados |
| **Postcondición** | Vista expandida visible |
| **Flujo alternativo** | 2a. Cierra → mini bar persiste |
| **Reglas de negocio** | RB-R02 |

### CU-H01: Ver saludo personalizado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-H01 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Post-login en Home |
| **Flujo principal** | 1. Home carga → 2. Sistema muestra saludo i18n time-based |
| **Postcondición** | Saludo visible |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-H01 |

### CU-H02: Ver KPIs resumen catálogo

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-H02 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Stats API disponible o degradada |
| **Flujo principal** | 1. Home fetch stats → 2. UI muestra KPIs |
| **Postcondición** | KPIs visibles |
| **Flujo alternativo** | 2a. API falla → degradación parcial (FR-H06) |
| **Reglas de negocio** | RB-H02 |

### CU-H03: Acceder shortcuts Home

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-H03 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Home cargado |
| **Flujo principal** | 1. Usuario navega secciones horizontales → 2. Accede playlists/recientes/top/géneros |
| **Postcondición** | Navegación o play desde shortcut |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-H01 |

### CU-H04: Continuar escuchando

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-H04 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Historial local con entradas (004/005) |
| **Flujo principal** | 1. Home muestra recientes → 2. Usuario retoma play |
| **Postcondición** | Reproducción desde historial |
| **Flujo alternativo** | 2a. Historial vacío → sección oculta/empty |
| **Reglas de negocio** | RB-H01 |

---


## User Scenarios & Testing *(mandatory)*

### User Story US-R01 — Controles básicos reproductor (Priority: P1)

Como **Usuario Registrado**, quiero **play, pause, volumen y barra progreso**, para **controlar la escucha**.

**Acceptance Scenarios**:

1. **Given** track seleccionado, **When** play, **Then** audio inicia (demo URL) y barra muestra progreso.
2. **When** pause, **Then** audio pausa; icono refleja estado.
3. **When** ajusta volumen, **Then** persiste en localStorage entre sesiones.
4. **When** seek, **Then** posición audio actualiza.

**Maps to**: CU-R01–R04 | FR-R01–R06

---

### User Story US-R02 — Cola y modos shuffle/repeat (Priority: P1)

Como **Usuario Registrado**, quiero **navegar cola con shuffle y repeat**, para **sesiones extended listening**.

**Acceptance Scenarios**:

1. **Given** múltiples tracks en cola, **When** next, **Then** reproduce siguiente.
2. **When** shuffle on, **Then** orden reproducción varía.
3. **When** repeat on, **Then** reinicia track/cola según modo.
4. **When** play playlist, **Then** cola = tracks playlist (002).

**Maps to**: CU-R05–R07 | FR-R07–R11

---

### User Story US-H01 — Hub Home operativo (Priority: P1)

Como **Usuario Registrado**, quiero **dashboard Home con resumen y accesos rápidos**, para **orientarme al entrar**.

**Acceptance Scenarios**:

1. **Given** login exitoso, **When** redirige `/dashboard`, **Then** ve saludo, KPIs, secciones horizontales.
2. **When** carga Home, **Then** muestra top tracks, géneros, playlists usuario, recientes.
3. **When** click item, **Then** navega o reproduce según contexto.
4. **When** stats API falla, **Then** degradación graceful parcial.

**Maps to**: CU-H01–H04 | FR-H01–H06

---

### User Story US-R03 — Now playing view (Priority: P2)

Como **Usuario Registrado**, quiero **vista expandida now-playing**, para **ver arte y controles ampliados**.

**Acceptance Scenarios**:

1. **When** expande player, **Then** modal/sheet con track info y controles.
2. **When** cierra, **Then** mini bar permanece.

**Maps to**: CU-R08 | FR-R12

---

### User Story US-R04 — Historial local escucha (Priority: P2)

Como **Usuario Registrado**, quiero **registrar tracks escuchados localmente**, para **"continuar escuchando"** en Home (unificación 005).

**Acceptance Scenarios**:

1. **When** completa play track, **Then** entrada en historial local por user.
2. **When** Home carga recientes, **Then** refleja historial.

**Maps to**: CU-R01 + integración 005 | FR-R13

---

### Edge Cases

- Demo audio asset missing: error user-friendly; no crash app.
- Play sin track: no-op o mensaje.
- Cambio rápido tracks: cancel previous load.
- Background tab: comportamiento HTML5 audio estándar documentado.

---

## Requirements *(mandatory)*

### Functional Requirements — Reproductor

- **FR-R01**: System MUST provide global persistent player bar en shell autenticado.
- **FR-R02**: MUST play/pause current track via HTML5 Audio.
- **FR-R03**: MUST map track ID → demo audio URL (Constitución: no backend stream).
- **FR-R04**: MUST persist volume preference locally.
- **FR-R05**: MUST support queue with next/previous.
- **FR-R06**: MUST support shuffle and repeat toggles.
- **FR-R07**: MUST accept PlayableTrack from catalog, playlist, favorites, search.
- **FR-R08**: MUST display current track metadata (title, artist, cover gradient).
- **FR-R09**: MUST show progress and allow seek when duration known.
- **FR-R10**: MUST populate queue from "play all" playlist action (002).
- **FR-R11**: MUST update playing state in UI reactively (signals).
- **FR-R12**: MUST provide expanded now-playing view.
- **FR-R13**: MUST append played tracks to local history service (005 integration).

### Functional Requirements — Home

- **FR-H01**: UI MUST provide `/dashboard` as default post-login landing.
- **FR-H02**: MUST display personalized greeting (i18n).
- **FR-H03**: MUST fetch and display stats summary KPIs.
- **FR-H04**: MUST show horizontal sections: recent, playlists, top tracks, genres, artists.
- **FR-H05**: MUST allow play action from Home cards/rows.
- **FR-H06**: MUST handle partial API failures without blank screen.

### Non-Functional Requirements

- **NFR-01**: Player bar MUST NOT unmount on route changes within shell.
- **NFR-02**: Play start ≤ 2s after user action with local demo assets.
- **NFR-03**: Home initial load ≤ 3s p95 with parallel API calls.
- **NFR-04**: MUST comply "no real streaming" product constraint (documented).

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-R01** | Audio source MUST be demo/local assets — NO backend streaming URL (Constitución §23.3). |
| **RB-R02** | Player MUST be available on all authenticated dashboard child routes. |
| **RB-R03** | Queue MUST NOT persist across browser sessions (v1) unless explicitly scoped future. |
| **RB-R04** | Volume MUST persist locally per browser. |
| **RB-H01** | Home MUST be default redirect after login (001) and `/` root. |
| **RB-H02** | Home KPIs MUST label si data synthetic cuando aplique (P10). |

### Key Entities

- **PlayableTrack**: id, title, artist, audioUrl, coverGradient.
- **PlayerState**: currentTrack, isPlaying, currentTime, duration, volume, shuffle, repeat, queue.
- **HomeSection**: typed content blocks (tracks, playlists, genres, KPIs).
- **HistoryEntry** (local): track ref, playedAt — ver 005.

---

## Criterios de Aceptación Globales

- **CA-001**: Play/pause/volume/seek operativos en player bar.
- **CA-002**: Queue next/prev/shuffle/repeat operativos.
- **CA-003**: Play from catalog, playlist, favorites, Home.
- **CA-004**: Home muestra secciones personalizadas post-login.
- **CA-005**: Demo audio constraint documentado en UI/help si asset missing.
- **CA-006**: Historial local alimenta sección recientes.

---

## Success Criteria *(mandatory)*

- **SC-001**: 95% play actions producen audio audible ≤ 2s (assets presentes).
- **SC-002**: 100% rutas shell muestran player bar.
- **SC-003**: 90% usuarios interactúan con Home en primera sesión.
- **SC-004**: 0 crashes player en cambio track consecutivo (100 ciclos test).

---

## Riesgos

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-001 | Demo assets missing in deploy | Package assets; CI check |
| R-002 | Expectativa streaming real | RB-R01 comunicación producto |
| R-003 | Home API fan-out lento | Parallel load, skeleton UI |
| R-004 | Historial split con 005 | Interface contract en plan |

---

## Dependencias

| Dep | Tipo |
|-----|------|
| 001 | Hard (auth shell) |
| 003 | Hard (track metadata) |
| 002 | Soft (play library) |
| 005 | Soft (history unify) |
| Stats API | Soft (Home KPIs) |

---

## Relación Constitución v1.0.0

| Ref | Aplicación |
|-----|------------|
| §1, §23.3 | No streaming real — RB-R01 |
| P2 | PKG-03 shared + streaming/home |
| P10 | Label synthetic KPIs on Home |
| §4.3 Operativo | OO-06, OO-07 |

---

## Out of Scope

- Streaming CDN / Spotify embed
- Lyrics display
- Gapless playback
- Catálogo navigation (003)
- Biblioteca CRUD (002)
- Analytics dashboards (007)

---

## Assumptions

- Demo WAV assets deployed under `/assets/audio/`.
- HTML5 Audio supported in target browsers.
- User authenticated for shell routes.

---

**Next Step**: `/speckit-plan`
