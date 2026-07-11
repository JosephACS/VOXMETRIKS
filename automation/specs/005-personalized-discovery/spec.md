# Feature Specification: Descubrimiento Personalizado e Historial Operativo

**Feature Branch**: `005-personalized-discovery`  
**Feature Directory**: `specs/005-personalized-discovery/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de recomendaciones personalizadas e historial unificado de actividad del usuario (escucha, búsquedas, timeline).

**Prerrequisitos:** `001-user-identity-access`; `003-catalog-discovery`; `004-listening-experience` (escritura historial escucha local); warehouse con `agg_recommendation_scores` y capa enterprise analytics.

**Delimitación vs otras specs (evitar duplicidad):**

| Dominio | Spec propietaria | Spec 005 |
|---------|------------------|----------|
| Auth / sesión | 001 | ❌ Consume identidad |
| Catálogo browse/search UI | 003 | ❌ Solo referencias track |
| Reproductor / cola / Home hub | 004 | ❌ Play vía 004 |
| Playlists / favoritos CRUD | 002 | ❌ Acciones contextuales |
| Perfil / prefs UI | 006 | ❌ |
| Recomendaciones + historial unificado | — | ✅ |

**Delimitación Constitución P10:** Datos de recomendación e historial warehouse MAY ser **synthetic** — MUST etiquetarse visiblemente al usuario.

---

## Contexto Empresarial

Voxmetriks posiciona la **personalización musical** como pilar estratégico (Constitución §2, OE-01, ES-02). Tras identidad (001), biblioteca (002), catálogo (003) y experiencia de escucha (004), el usuario MUST poder **descubrir música alineada a su perfil** y **consultar su actividad pasada** de forma coherente.

La auditoría arquitectónica confirmó:

- Rutas UI `/recommendations` y `/history` con tabs (música, usuario, búsqueda).
- API `/analytics/recommendations` y `/analytics/history` (hub unificado warehouse).
- Scores en `agg_recommendation_scores` generados por capa enterprise (potencialmente synthetic).
- Historial de escucha en `HistoryService` (localStorage, keyed por user).
- Historial de búsqueda en `SearchHistoryService` (local) mezclado con datos warehouse en hub.

Sin especificación formal, la personalización opera con **comportamiento implícito**, **historial fragmentado** y **riesgo de interpretación errónea** de datos synthetic como telemetría real del usuario — violación potencial de P10 y ES-07.

Esta spec gobierna la **capacidad operativa de descubrimiento personalizado e historial**, definiendo comportamiento requerido del producto independiente de detalles de implementación actual.

---

## Problema

### Situación actual

Usuarios autenticados necesitan:

1. **Descubrir** música recomendada basada en scores disponibles (genéricos o user-aware).
2. **Retomar** escucha reciente sin depender solo del Home (004).
3. **Revisar** búsquedas y actividad para entender su uso de la plataforma.
4. **Confiar** en que las recomendaciones no se presentan como basadas en escucha real si los datos son synthetic.

Riesgos sin especificación formal:

- Historial escucha (local) vs timeline warehouse vs búsquedas locales — **tres fuentes sin contrato unificado**.
- API recomendaciones acepta auth opcional — reglas de personalización no documentadas.
- Acciones play/favorite desde recommendations/history sin trazabilidad a 002/004.
- Sin métricas empresariales (M-8A/B, M-9A/B) ni criterios de aceptación auditables.

### Problema de negocio

**Los usuarios no pueden declarar Voxmetriks como plataforma que "me conoce"** si recomendaciones e historial carecen de reglas operativas explícitas, trazabilidad empresarial y transparencia sobre origen de datos — reduciendo engagement y confianza del producto personalizado.

---

## Objetivo

Gobernar la **capacidad operativa de Descubrimiento Personalizado e Historial** en Voxmetriks:

1. Presentar recomendaciones personalizadas (mejoradas con identidad autenticada cuando disponible).
2. Unificar presentación de historial operativo: escucha, actividad usuario, búsquedas.
3. Etiquetar origen de datos (local, warehouse, synthetic) según Constitución P10.
4. Habilitar acciones contextuales play (004) y favorite (002) desde recomendaciones e historial.
5. Garantizar aislamiento de historial local por usuario (001 identity key).
6. Establecer trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU completa.

**Resultado esperado:** usuario autenticado explora recomendaciones y consulta historial con UX predecible, datos transparentes y acciones integradas con biblioteca y reproductor.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma referencia: experiencia musical personalizada + analítica gobernada |
| **OT-05** | Objetivo Táctico | Habilitar capa de personalización consumiendo agregados warehouse y datos locales de actividad |
| **OO-08** | Objetivo Operativo | Consumir y presentar recomendaciones personalizadas al usuario |
| **OO-09** | Objetivo Operativo | Consultar historial unificado de actividad (escucha, usuario, búsqueda) |
| **M-8A** | Meta | Panel recomendaciones muestra ≥ 1 lista con tracks válidos del catálogo |
| **M-8B** | Meta | Autenticación mejora personalización cuando user_id disponible en API |
| **M-9A** | Meta | Historial presenta 3 categorías distinguibles (música, usuario, búsqueda) |
| **M-9B** | Meta | 100% entradas historial trazables a fuente declarada (local/warehouse/synthetic) |
| **DEP-03** | Departamento | **Producto Personalización** |
| **PKG-04** | Paquete | `recommendations`, `history` (frontend); `/analytics/recommendations`, `/analytics/history` (backend analytics) |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-RC01 | US-RC01 | FR-RC01 | CA-001 |
| CU-RC01 | US-RC01 | FR-RC03 | CA-001 |
| CU-RC01 | US-RC01 | FR-RC04 | CA-001 |
| CU-RC01 | US-RC01 | FR-RC06 | CA-001 |
| CU-RC01 | US-RC01 | FR-RC08 | CA-001 |
| CU-RC02 | US-RC01 | FR-RC02 | CA-001 |
| CU-RC02 | US-RC01 | FR-RC05 | CA-002 |
| CU-RC03 | US-RC02 | FR-RC07 | CA-006 |
| CU-RC04 | US-RC02 | FR-RC07 | CA-007 |
| CU-HI01 | US-HI01 | FR-HI01 | CA-003 |
| CU-HI01 | US-HI01 | FR-HI02 | CA-004 |
| CU-HI01 | US-HI01 | FR-HI03 | CA-003 |
| CU-HI01 | US-HI01 | FR-HI03 | CA-004 |
| CU-HI04 | US-HI02 | FR-HI01 | CA-003 |
| CU-HI04 | US-HI02 | FR-HI07 | CA-003 |
| CU-HI02 | US-HI02 | FR-HI04 | CA-005 |
| CU-HI02 | US-HI02 | FR-HI05 | CA-005 |
| CU-HI03 | US-HI02 | FR-HI06 | CA-003 |
| CU-HI03 | US-HI02 | FR-HI06 | CA-005 |
| CU-HI02 | US-HI02 | FR-HI08 | CA-005 |
| CU-HI01 | US-HI03 | FR-HI09 | CA-006 |
| CU-HI05 | US-HI04 | FR-HI10 | CA-003 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | 005 | Pendiente |
| OE-01 | OT-05 | OO-08 | M-8B | DEP-03 | PKG-04 | CU-RC02 | US-RC01 | 005 | Pendiente |
| OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC02 | US-RC01 | 005 | Pendiente |
| OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC03 | US-RC02 | 005 | Pendiente |
| OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC04 | US-RC02 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI04 | US-HI02 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI02 | US-HI02 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI03 | US-HI02 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI03 | 005 | Pendiente |
| OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI05 | US-HI04 | 005 | Pendiente |
## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Registrado Autenticado** | Consume recomendaciones e historial completo con hub warehouse | Descubrir música; revisar actividad; play/favorite |
| **Usuario Visitante (API only)** | Puede consumir recomendaciones genéricas vía API sin token | Exploración limitada — no historial warehouse |
| **Sistema Voxmetriks** | Agrega local + warehouse; aplica scores; etiqueta fuentes | Cumplir P10; aislar datos por user |
| **Capa Enterprise Analytics** | Provee agg_recommendation_scores y facts synthetic | Fuente de datos — no actor UI directo |

---

## Casos de Uso

### CU-RC01: Ver listas recomendaciones

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-RC01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida; agg scores o empty |
| **Flujo principal** | 1. Usuario abre recommendations → 2. Sistema sirve listas con tracks |
| **Postcondición** | Listas visibles o empty state |
| **Flujo alternativo** | 2a. Agg vacío → empty state (FR-RC06) |
| **Reglas de negocio** | RB-RC01, RB-RC04 |

### CU-RC02: Ver recomendaciones user-aware

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-RC02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Bearer token en API |
| **Flujo principal** | 1. API recibe auth → 2. Scores scoped user_id |
| **Postcondición** | Personalización aplicada |
| **Flujo alternativo** | 2a. Sin token → genérico (RB-RC03) |
| **Reglas de negocio** | RB-RC02, RB-RC03 |

### CU-RC03: Reproducir track recomendado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-RC03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Track en lista |
| **Flujo principal** | 1. Usuario play → 2. Invoca reproductor 004 |
| **Postcondición** | Reproducción activa |
| **Flujo alternativo** | 2a. Track inválido → error graceful |
| **Reglas de negocio** | RB-RC04 |

### CU-RC04: Favoritar desde recomendaciones

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-RC04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Track en lista |
| **Flujo principal** | 1. Usuario favorita → 2. Invoca API 002 |
| **Postcondición** | Favorito persistido |
| **Flujo alternativo** | 2a. Ya favorito → idempotente |
| **Reglas de negocio** | RB-RC04 |

### CU-HI01: Ver historial escucha

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HI01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Tab música → 2. Carga historial local por user key |
| **Postcondición** | Entradas escucha visibles |
| **Flujo alternativo** | 2a. Vacío → empty state |
| **Reglas de negocio** | RB-HI01, RB-HI06 |

### CU-HI02: Ver timeline actividad usuario

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HI02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Hub API accesible |
| **Flujo principal** | 1. Tab usuario → 2. Fetch hub → 3. Timeline scoped user |
| **Postcondición** | Actividad warehouse visible |
| **Flujo alternativo** | 2a. 401 → solo local; 2b. Error → degradación |
| **Reglas de negocio** | RB-HI02, RB-HI04 |

### CU-HI03: Ver historial búsquedas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HI03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Datos local y/o warehouse |
| **Flujo principal** | 1. Tab búsqueda → 2. Merge local + hub |
| **Postcondición** | Búsquedas pasadas visibles |
| **Flujo alternativo** | 2a. Duplicados → dedup en plan (RB-HI03) |
| **Reglas de negocio** | RB-HI03, RB-HI06 |

### CU-HI04: Cambiar tabs historial

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HI04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | En pantalla history |
| **Flujo principal** | 1. Usuario cambia tab → 2. UI carga contenido tab |
| **Postcondición** | Tab activo con counts |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-HI06 |

### CU-HI05: Limpiar historial local

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-HI05 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Entradas locales existentes |
| **Flujo principal** | 1. Usuario clear local → 2. Sistema elimina solo local |
| **Postcondición** | Local vacío; warehouse intacto |
| **Flujo alternativo** | 2a. Sin entradas → no-op |
| **Reglas de negocio** | RB-HI05 |

---


## User Scenarios & Testing *(mandatory)*

### User Story US-RC01 — Ver recomendaciones personalizadas (Priority: P1)

Como **Usuario Registrado**, quiero **ver tracks recomendados para mí en `/recommendations`**, para **descubrir música alineada a mi perfil operativo**.

**Why this priority**: Core valor personalización post-biblioteca; entregable principal del dominio OO-08.

**Independent Test**: Usuario autenticado abre `/recommendations`; ve ≥ 1 lista con tracks; play inicia reproductor sin navegar catálogo.

**Acceptance Scenarios**:

1. **Given** usuario autenticado en `/recommendations`, **When** página carga, **Then** muestra listas de recomendación con title, tracks, metadata (artista, duración).
2. **Given** scores de capa enterprise synthetic, **When** listas renderizan, **Then** UI muestra disclaimer visible "basado en datos de demostración" o equivalente i18n (P10).
3. **Given** request API con Bearer token, **When** backend procesa, **Then** personalización usa user_id del token (M-8B).
4. **Given** request API sin token, **When** backend procesa, **Then** retorna recomendaciones genéricas sin error (RB-RC03).
5. **Given** agg vacío o sin datos, **When** carga, **Then** empty state claro sin error 500.

**Maps to**: CU-RC01, CU-RC02 | FR-RC01–FR-RC06 | M-8A, M-8B

---

### User Story US-RC02 — Reproducir y favoritar desde recomendaciones (Priority: P1)

Como **Usuario Registrado**, quiero **reproducir o favoritar tracks desde recomendaciones**, para **actuar sobre descubrimiento sin fricción**.

**Why this priority**: Cierra loop descubrimiento → escucha → biblioteca; dependencia directa 002/004.

**Independent Test**: Play track desde card recomendación; verificar player bar activo; favoritar y verificar en `/liked`.

**Acceptance Scenarios**:

1. **Given** track en lista recomendaciones, **When** usuario pulsa play, **Then** MusicPlayerService (004) reproduce track.
2. **Given** track no favorito, **When** pulsa favorito, **Then** API favoritos (002) persiste relación.
3. **Given** track ya favorito, **When** pulsa favorito, **Then** estado UI coherente con 002 (toggle/idempotente).

**Maps to**: CU-RC03, CU-RC04 | FR-RC07 | M-8A

---

### User Story US-HI01 — Historial de escucha unificado (Priority: P1)

Como **Usuario Registrado**, quiero **ver qué he escuchado recientemente en tab música de `/history`**, para **retomar sesiones de escucha**.

**Why this priority**: Materializa OO-09; integración directa con FR-R13 de spec 004.

**Independent Test**: Reproducir 3 tracks; abrir `/history` tab música; ver 3 entradas ordenadas por recencia.

**Acceptance Scenarios**:

1. **Given** usuario autenticado, **When** abre tab música, **Then** muestra entradas de HistoryService keyed por user id.
2. **Given** play completado en 004, **When** usuario abre historial, **Then** nueva entrada visible con track metadata y timestamp.
3. **Given** datos warehouse de escucha disponibles en hub, **When** tab carga, **Then** merge o sección separada documentada en plan (sin duplicar confusamente).
4. **Given** usuario A y B en mismo browser secuencial, **When** cada uno consulta historial, **Then** no ven entradas del otro (NFR-03).

**Maps to**: CU-HI01 | FR-HI01–FR-HI03 | M-9A, M-9B

---

### User Story US-HI02 — Historial actividad y búsquedas (Priority: P2)

Como **Usuario Registrado**, quiero **ver mi actividad en plataforma y búsquedas pasadas**, para **entender mi patrón de uso**.

**Why this priority**: Completa valor historial hub; depende de warehouse enterprise.

**Independent Test**: Autenticado abre tabs usuario y búsqueda; datos visibles o empty state; fallback si API falla.

**Acceptance Scenarios**:

1. **Given** tab usuario, **When** hub API responde, **Then** timeline warehouse scoped al user autenticado.
2. **Given** tab búsqueda, **When** carga, **Then** combina SearchHistoryService local + búsquedas warehouse.
3. **Given** hub API error (5xx/timeout), **When** tab carga, **Then** muestra datos locales disponibles + mensaje degradación (FR-HI08).
4. **Given** sesión inválida, **When** solicita hub warehouse, **Then** 401 — tab muestra solo local o redirect según plan.

**Maps to**: CU-HI02, CU-HI03, CU-HI04 | FR-HI04–FR-HI08 | M-9A, M-9B

---

### User Story US-HI03 — Acciones desde historial (Priority: P2)

Como **Usuario Registrado**, quiero **reproducir tracks desde entradas de historial**, para **retomar escucha con un click**.

**Independent Test**: Click play en entrada historial música; reproductor inicia track correcto.

**Acceptance Scenarios**:

1. **Given** entrada historial escucha, **When** play, **Then** 004 reproduce track referenciado.
2. **Given** entrada búsqueda, **When** click query, **Then** navega a búsqueda 003 con query pre-filled (si soportado en plan).

**Maps to**: CU-HI01 | FR-HI09

---

### User Story US-HI04 — Limpiar historial local (Priority: P3)

Como **Usuario Registrado**, quiero **limpiar mi historial local de escucha/búsqueda**, para **controlar privacidad en dispositivo**.

**Acceptance Scenarios**:

1. **Given** historial local con entradas, **When** ejecuta clear local, **Then** entradas local eliminadas.
2. **Given** clear local, **When** warehouse hub consultado, **Then** datos warehouse persisten (RB-HI05).

**Maps to**: CU-HI05 | FR-HI10

---

### Edge Cases

- Warehouse sin `agg_recommendation_scores`: empty state recomendaciones con mensaje orientador.
- Usuario nuevo sin historial: empty states por tab con CTA a catálogo/Home.
- localStorage cleared: historial local vacío; warehouse persiste si auth válida.
- Synthetic disclaimer MUST NOT implicar telemetría real del usuario (P10).
- Track recomendado eliminado del catálogo: card graceful (sin play) o 404 en play.
- Sesión expirada mid-fetch hub: degradación a local-only.

---

## Requirements *(mandatory)*

### Functional Requirements — Recomendaciones

- **FR-RC01**: System MUST expose recommendations via API returning lists of tracks with catalog metadata.
- **FR-RC02**: API MUST accept optional Bearer authentication; when present MUST scope personalization to authenticated user_id.
- **FR-RC03**: UI MUST provide authenticated route `/recommendations`.
- **FR-RC04**: UI MUST display sufficient track metadata for play, favorite, and navigation to track detail (003).
- **FR-RC05**: UI MUST display visible synthetic/demo labeling when recommendation scores originate from enterprise synthetic layer (Constitución P10).
- **FR-RC06**: System MUST handle empty recommendation results with user-friendly empty state.
- **FR-RC07**: UI MUST integrate play action with music player (004) and favorite action with favorites API (002).
- **FR-RC08**: System MUST source recommendation scores from warehouse aggregate layer (`agg_recommendation_scores`) — read-only.

### Functional Requirements — Historial

- **FR-HI01**: UI MUST provide `/history` with three tabs: music, user activity, search.
- **FR-HI02**: System MUST persist play history locally per authenticated user identity key (written by 004 FR-R13).
- **FR-HI03**: Tab music MUST load and display local play history entries ordered by recency.
- **FR-HI04**: When authenticated, system MUST fetch unified history hub from `/analytics/history`.
- **FR-HI05**: Tab user MUST display warehouse user activity timeline from hub response.
- **FR-HI06**: Tab search MUST merge local search history with warehouse search entries.
- **FR-HI07**: UI MUST display entry counts per tab.
- **FR-HI08**: When hub API fails, UI MUST degrade gracefully showing local data where available.
- **FR-HI09**: UI MUST allow play from music history entries via music player (004).
- **FR-HI10**: UI MAY provide clear-local-history action for local stores only; MUST NOT delete warehouse facts.

### Non-Functional Requirements

- **NFR-01**: Recommendations page MUST load ≤ 3s p95.
- **NFR-02**: History hub MUST load ≤ 3s p95 when authenticated.
- **NFR-03**: Local history MUST NOT leak between users — storage key MUST include user identity from 001.
- **NFR-04**: Synthetic labeling MUST be accessible (WCAG: not tooltip-only; visible text or badge).
- **NFR-05**: Recommendation/history reads MUST NOT mutate warehouse ELT tables (Constitución P6).
- **NFR-06**: Hub warehouse endpoints requiring auth MUST return 401 without valid session (001).

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-RC01** | Recommendations sourced from `agg_recommendation_scores` MAY be synthetic — MUST disclose to user (P10). |
| **RB-RC02** | When auth present, personalized recommendation path MUST use authenticated user_id. |
| **RB-RC03** | Generic recommendations MUST be available without authentication at API level. |
| **RB-RC04** | Recommended tracks MUST reference valid catalog track IDs (003). |
| **RB-HI01** | Local history MUST be scoped per authenticated user identity; cleared on logout client-side key isolation. |
| **RB-HI02** | Warehouse history hub MUST require valid session; MUST NOT return other users' activity. |
| **RB-HI03** | Merged search history MUST NOT show duplicate entries without dedup strategy defined in plan. |
| **RB-HI04** | Historial MUST NOT expose activity of other users under any condition. |
| **RB-HI05** | Clear local history MUST NOT delete warehouse persisted facts. |
| **RB-HI06** | Each history entry MUST declare traceable source: `local_music`, `local_search`, `warehouse`, or `synthetic`. |

### Key Entities

- **RecommendationList**: id, title, description?, tracks[], scoreSource (synthetic|computed), generatedAt.
- **RecommendationTrack**: trackId, title, artist, score?, rank.
- **HistoryHub**: userTimeline[], searchEntries[], metadata (sources[]).
- **HistoryEntry** (local music): trackId, title, artist, playedAt, source=`local_music`.
- **SearchHistoryEntry**: query, timestamp, source (`local_search`|`warehouse`).
- **UserActivityEvent** (warehouse): eventType, timestamp, payload summary, source=`warehouse`|`synthetic`.

---

## Criterios de Aceptación Globales (Feature)

- **CA-001**: `/recommendations` funcional para usuario autenticado con ≥ 1 lista o empty state.
- **CA-002**: Disclaimer synthetic visible cuando scores enterprise synthetic (P10).
- **CA-003**: `/history` tres tabs operativos con counts.
- **CA-004**: Historial escucha local integrado con escritura 004 y lectura 005.
- **CA-005**: Hub `/analytics/history` integrado con fallback local en fallo.
- **CA-006**: Play desde recomendaciones e historial operativo vía 004.
- **CA-007**: Favorite desde recomendaciones operativo vía 002.
- **CA-008**: 0 filtración historial cross-user en pruebas aislamiento.
- **CA-009**: Trazabilidad matriz OE→HU completa documentada.

---

## Success Criteria *(mandatory)*

- **SC-001**: 80% usuarios autenticados ven ≥ 5 tracks recomendados en primera visita a `/recommendations`.
- **SC-002**: 100% sesiones con data synthetic muestran disclaimer visible (auditoría UI).
- **SC-003**: 90% usuarios con ≥ 3 plays en sesión ven entradas en tab música historial.
- **SC-004**: 0 entradas historial local cruzadas entre usuarios en suite aislamiento (NFR-03).
- **SC-005**: 95% cargas hub history completan ≤ 3s p95 en entorno demo poblado.

---

## Riesgos

| ID | Riesgo | Prob. | Impacto | Mitigación |
|----|--------|-------|---------|------------|
| R-001 | Usuario interpreta synthetic como escucha real | Media | Alto | RB-RC01, FR-RC05, P10 |
| R-002 | Historial dual confunde (local vs warehouse) | Alta | Medio | RB-HI06, UX merge strategy en plan |
| R-003 | agg_recommendation_scores vacío post-ELT | Media | Medio | FR-RC06 empty state |
| R-004 | Privacidad GDPR futura | Baja | Alto | RB-HI04, privacy_public 001/006 |
| R-005 | Hub API lento bloquea historial | Media | Medio | FR-HI08 degradación |
| R-006 | Dependencia 004 no escribe historial | Alta | Alto | Contract FR-R13 ↔ FR-HI02 en plan conjunto |

---

## Dependencias

| Dependencia | Tipo | Referencia |
|-------------|------|------------|
| Identidad y acceso | Hard | `001-user-identity-access` |
| Catálogo tracks | Hard | `003-catalog-discovery` |
| Experiencia escucha | Hard | `004-listening-experience` (history write, play) |
| Biblioteca favoritos | Soft | `002-personal-music-library` |
| agg_recommendation_scores | Hard | Capa enterprise / TA-18 |
| enterprise_analytics synthetic | Data | Constitución ES-07, P10 |

---

## Relación con Constitución v1.0.0

| Sección | Aplicación |
|---------|------------|
| §2 ES-02 Personalización | Objetivo y OO-08 |
| §5 P6 Warehouse vs app | NFR-05: reads warehouse; local history in client app layer |
| §5 P10 Synthetic boundary | FR-RC05, RB-RC01, RB-HI06 |
| §5 ES-07 Synthetic governance | Disclaimer obligatorio |
| §12 Trazabilidad | Matriz completa OE→Impl |
| §4.3 Nivel operativo | OO-08, OO-09 |

---

## Out of Scope

- Entrenamiento ML / collaborative filtering en tiempo real
- Persistencia server-side unificada de historial escucha (v1: merge UX; persistencia futura spec)
- Analytics dashboards enterprise (007)
- Registro/login (001)
- Catálogo browse/search UI (003)
- Reproductor/controles (004)
- Playlists CRUD (002)

---

## Assumptions

- Capa enterprise ejecutada generando `agg_recommendation_scores` (puede ser synthetic).
- Usuario acepta disclosure de naturaleza demo/synthetic en personalización.
- localStorage disponible en browsers objetivo.
- Auth Bearer operativo según spec 001.

---

**Next Step**: `/speckit-plan` — Constitution Check P6, P10; contract FR-R13 ↔ FR-HI02 con spec 004.
