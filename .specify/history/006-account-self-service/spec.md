> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Autogestión de Cuenta y Preferencias

**Feature Branch**: `006-account-self-service`  
**Feature Directory**: `specs/006-account-self-service/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Capacidad operativa de autogestión post-autenticación: pantalla perfil UI, configuración de cuenta, preferencias de experiencia y visibilidad operativa del sistema.

**Prerrequisito:** `specs/001-user-identity-access/` — autenticación, API perfil GET/PATCH `/users/me`, guards y rol engineer MUST estar operativos.

**Delimitación vs 001 (CRÍTICA — evitar duplicidad):**

| Dominio | Spec 001 (propietaria) | Spec 006 (propietaria) |
|---------|------------------------|------------------------|
| Registro / Login / Logout | ✅ CU-01, CU-02, CU-05 | ❌ |
| Emisión sesión / tokens | ✅ CU-07 | ❌ |
| Guards auth/guest | ✅ CU-06 | ❌ Consume resultado |
| API contrato `/users/me` GET/PATCH | ✅ Define contrato backend | ✅ Define **UX consumo** y sincronización |
| Rol engineer gating (RB-015) | ✅ US-07 | ❌ Consume para tabs settings |
| Pantalla `/users` perfil visual | ❌ | ✅ CU-PF01–PF03 |
| Pantalla `/settings` | ❌ | ✅ CU-ST01–ST06 |
| UI prefs locales (theme, language, KPI toggles) | ❌ | ✅ |
| Health API/warehouse display en settings | ❌ | ✅ |
| Sincronización prefs UI ↔ backend `preferences_json` | ❌ (CU-04 API only) | ✅ Estrategia UX |

**Delimitación vs 002:** Stats biblioteca en perfil son **lectura** — CRUD playlists/favoritos permanece en 002.

**Delimitación vs 005:** Historial/recomendaciones NO incluidos — solo prefs `recommendations_enabled` como toggle negocio.

---

## Contexto Empresarial

Tras establecer identidad (001), el usuario MUST **autogestionar** su relación operativa con Voxmetriks: visualizar identidad, ajustar preferencias de experiencia (tema, idioma, calidad audio, privacidad, recomendaciones) y, cuando corresponda, observar estado técnico del sistema (health API, warehouse, pipeline).

La auditoría confirmó:

- Ruta `/users` con componente perfil consumiendo API.
- Ruta `/settings` con tabs: general, api, warehouse, pipeline (últimos dos gated engineer).
- `UiPreferencesService` — tema dark/light/system, toggles KPI locales en localStorage.
- `I18nService` — ES/EN.
- Dual store: prefs UI local vs `preferences_json` backend (001 CU-04).

Constitución: i18n ES/EN (TA-11), design system con tema (TA-12), engineer access (001 RB-015), no secrets in UI (§18).

Esta spec gobierna **autogestión operativa de cuenta** sin redefinir ciclo de identidad ni mutaciones de biblioteca.

---

## Problema

### Situación actual

Usuarios autenticados necesitan:

1. **Visualizar** identidad y resumen biblioteca en pantalla dedicada (`/users`).
2. **Configurar** tema e idioma sin reiniciar sesión.
3. **Persistir** preferencias de negocio en servidor para consistencia cross-device (target v1).
4. **Entender** disponibilidad del sistema vía health en settings.
5. **Acceder** (engineer) a tabs warehouse/pipeline desde settings.

Riesgos sin especificación formal:

- Perfil API (001 CU-03) vs UI perfil (006) — **responsabilidades no delimitadas**.
- Tema UI local vs `dark_mode` backend — **drift sin regla de precedencia**.
- Settings tabs engineer pueden divergir de guards 001.
- Sin trazabilidad OE→HU para autogestión (OO-10, OO-11).

### Problema de negocio

**Los usuarios no pueden operar Voxmetriks de forma autónoma y predecible** si perfil, settings y preferencias carecen de reglas empresariales unificadas — aumentando fricción, soporte y inconsistencia de experiencia personalizada.

---

## Objetivo

Gobernar la **capacidad operativa de Autogestión de Cuenta y Preferencias** en Voxmetriks:

1. Pantalla perfil (`/users`) consumiendo API perfil con stats biblioteca (002).
2. Pantalla settings (`/settings`) con tabs autogestión y health.
3. Gestionar tema, idioma y preferencias UI locales.
4. Sincronizar preferencias de negocio con backend PATCH `/users/me/preferences` (001).
5. Mostrar health sistema para transparencia operativa.
6. Gating engineer tabs alineado con 001 RB-015.
7. Trazabilidad OE→OT→OO→Meta→Departamento→Paquete→CU→HU completa.

**Resultado esperado:** usuario autenticado gestiona perfil y preferencias con UX coherente, prefs negocio persistidas en servidor, y cero duplicidad con flujos auth de 001.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Plataforma referencia: experiencia personalizada gobernada |
| **OT-06** | Objetivo Táctico | Habilitar capa autogestión cuenta en SPA post-autenticación |
| **OO-10** | Objetivo Operativo | Configurar preferencias operativas de cuenta y UI |
| **OO-11** | Objetivo Operativo | Visualizar perfil e identidad operativa en UI dedicada |
| **M-10A** | Meta | 100% preferencias negocio válidas persisten vía API tras guardar |
| **M-10B** | Meta | Tema/idioma aplican en ≤ 1s tras cambio usuario |
| **M-11A** | Meta | Perfil UI muestra stats biblioteca actualizados (favorites_count, playlists_count) |
| **DEP-01** | Departamento | **Plataforma de Producto** |
| **PKG-05** | Paquete | `packages/users` (profile UI), `packages/administration/settings`, `core/ui-preferences`, `core/i18n` |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../README.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-PF01 | US-PF01 | FR-PF01 | CA-001 |
| CU-PF01 | US-PF01 | FR-PF02 | CA-001 |
| CU-PF01 | US-PF01 | FR-PF03 | CA-001 |
| CU-PF02 | US-PF01 | FR-PF04 | CA-002 |
| CU-PF03 | US-PF02 | FR-PF05 | CA-001 |
| CU-ST01 | US-ST01 | FR-ST01 | CA-003 |
| CU-ST01 | US-ST01 | FR-ST02 | CA-003 |
| CU-ST02 | US-ST01 | FR-ST03 | CA-003 |
| CU-ST01 | US-ST01 | FR-ST04 | CA-003 |
| CU-ST03 | US-ST02 | FR-ST05 | CA-004 |
| CU-ST03 | US-ST02 | FR-ST06 | CA-004 |
| CU-ST03 | US-ST02 | FR-ST08 | CA-004 |
| CU-ST04 | US-ST03 | FR-ST07 | CA-003 |
| CU-ST04 | US-ST03 | FR-ST04 | CA-003 |
| CU-ST05 | US-ST04 | FR-ST09 | CA-005 |
| CU-ST05 | US-ST04 | FR-ST10 | CA-005 |
| CU-ST06 | US-ST05 | FR-ST11 | CA-006 |
| CU-ST01 | US-ST01 | FR-ST12 | CA-007 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF01 | US-PF01 | 006 | Pendiente |
| OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF02 | US-PF01 | 006 | Pendiente |
| OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF03 | US-PF02 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST02 | US-ST01 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST03 | US-ST02 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST04 | US-ST03 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST05 | US-ST04 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST06 | US-ST05 | 006 | Pendiente |
| OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | 006 | Pendiente |
## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Registrado Autenticado** | Gestiona perfil y settings | Autonomía; personalización |
| **Usuario Engineer** | Accede tabs warehouse/pipeline en settings | Visibilidad datos (001 RB-015) |
| **Sistema Voxmetriks** | Persiste prefs API + local; fetch health | Coherencia; seguridad |
| **API Perfil (001)** | Fuente autoritativa identidad y prefs negocio | Contrato backend — actor indirecto |

---

## Casos de Uso

### CU-PF01: Ver pantalla perfil con identidad

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PF01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Sesión válida (001) |
| **Flujo principal** | 1. Usuario abre /users → 2. GET /users/me → 3. UI identidad sin secrets |
| **Postcondición** | Perfil identidad visible |
| **Flujo alternativo** | 2a. Sin sesión → redirect login |
| **Reglas de negocio** | RB-PF01, RB-PF02 |

### CU-PF02: Ver stats biblioteca en perfil

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PF02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | API perfil responde |
| **Flujo principal** | 1. UI muestra favorites_count y playlists_count de API |
| **Postcondición** | Stats coherentes con 002 |
| **Flujo alternativo** | 2a. API error → mensaje retry |
| **Reglas de negocio** | RB-PF02 |

### CU-PF03: Ver preview playlists recientes

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-PF03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Usuario tiene playlists |
| **Flujo principal** | 1. API incluye preview → 2. UI muestra hasta 6 items |
| **Postcondición** | Preview visible |
| **Flujo alternativo** | 2a. Sin playlists → empty state |
| **Reglas de negocio** | RB-PF02 |

### CU-ST01: Cambiar tema

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST01 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | En settings general |
| **Flujo principal** | 1. Usuario selecciona tema → 2. UI aplica y persiste local |
| **Postcondición** | Tema activo ≤1s |
| **Flujo alternativo** | 2a. Conflicto dark_mode API → RB-ST05 |
| **Reglas de negocio** | RB-ST03, RB-ST05 |

### CU-ST02: Cambiar idioma ES/EN

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST02 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | En settings |
| **Flujo principal** | 1. Usuario cambia idioma → 2. I18nService actualiza strings |
| **Postcondición** | Idioma persistido local |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-ST02 |

### CU-ST03: Actualizar prefs negocio vía API

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST03 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Campos válidos 001 RB-010 |
| **Flujo principal** | 1. Usuario modifica toggles → 2. PATCH preferences → 3. Confirmación |
| **Postcondición** | preferences_json actualizado |
| **Flujo alternativo** | 2a. PATCH inválido → error UI |
| **Reglas de negocio** | RB-ST01, RB-ST04 |

### CU-ST04: Configurar toggles KPI locales

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST04 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | En settings |
| **Flujo principal** | 1. Usuario toggle KPI → 2. UiPreferences persiste |
| **Postcondición** | Home respeta toggles (004) |
| **Flujo alternativo** | — |
| **Reglas de negocio** | RB-ST02 |

### CU-ST05: Ver health API

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST05 |
| **Actor principal** | Usuario Registrado Autenticado |
| **Precondición** | Tab api settings |
| **Flujo principal** | 1. Fetch /health → 2. UI status sin secrets |
| **Postcondición** | Health visible |
| **Flujo alternativo** | 2a. Error → mensaje sin stack trace (RB-ST06) |
| **Reglas de negocio** | RB-ST06 |

### CU-ST06: Ver warehouse/pipeline engineer

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-ST06 |
| **Actor principal** | Usuario Engineer |
| **Precondición** | Rol engineer 001 RB-015 |
| **Flujo principal** | 1. Engineer abre tabs → 2. UI estado datos read-only |
| **Postcondición** | Tabs visibles solo engineer |
| **Flujo alternativo** | 2a. Usuario estándar → tabs ocultas |
| **Reglas de negocio** | RB-ST06 |

---


## User Scenarios & Testing *(mandatory)*

### User Story US-PF01 — Ver perfil de usuario (Priority: P1)

Como **Usuario Registrado**, quiero **ver mi perfil en `/users` con stats de biblioteca**, para **entender mi cuenta operativa en Voxmetriks**.

**Why this priority**: Centro visual de identidad post-login; materializa OO-11.

**Independent Test**: Autenticado navega `/users`; ve identidad sin password; stats playlists/favoritos coherentes con 002.

**Acceptance Scenarios**:

1. **Given** sesión válida, **When** abre `/users`, **Then** muestra username, email, plan, favorite_genre, preferences summary.
2. **Given** API `/users/me`, **When** responde, **Then** favorites_count y playlists_count reflejan estado real biblioteca (002).
3. **Given** playlists existentes, **When** perfil carga, **Then** preview hasta 6 playlists con nombre.
4. **Given** sesión inválida, **When** navega `/users`, **Then** redirect login (001 CU-06).
5. **Given** perfil renderizado, **When** inspecciona DOM, **Then** no expone password ni hash (NFR-03).

**Maps to**: CU-PF01, CU-PF02 | FR-PF01–FR-PF04 | M-11A

---


### User Story US-PF02 — Preview playlists recientes (Priority: P2)

Como **Usuario Registrado**, quiero **ver un preview de mis playlists recientes en perfil**, para **acceder rápidamente a mi biblioteca**.

**Independent Test**: Usuario con ≥1 playlist ve hasta 6 items en preview.

**Acceptance Scenarios**:

1. **Given** playlists en API preview, **When** perfil carga, **Then** muestra hasta 6 nombres.
2. **Given** sin playlists, **When** perfil carga, **Then** empty state sin error.

**Maps to**: CU-PF03 | FR-PF05 | M-11A

---

### User Story US-ST01 — Tema e idioma (Priority: P1)

Como **Usuario Registrado**, quiero **cambiar tema e idioma en settings**, para **adaptar la interfaz a mi preferencia**.

**Why this priority**: Impacto inmediato UX; TA-11 i18n; independiente de API.

**Independent Test**: Cambiar tema a light y idioma EN; verificar aplicación inmediata; recargar — prefs persisten.

**Acceptance Scenarios**:

1. **Given** settings general, **When** selecciona tema dark/light/system, **Then** UI aplica en ≤ 1s (M-10B).
2. **Given** settings, **When** cambia idioma ES↔EN, **Then** strings settings y shell actualizan vía I18nService.
3. **Given** cambio tema/idioma, **When** recarga página, **Then** preferencias UI persisten en localStorage.
4. **Given** tema system, **When** OS preference cambia, **Then** UI sigue preferencia sistema (si soportado).

**Maps to**: CU-ST01, CU-ST02 | FR-ST01–FR-ST04 | M-10B

---

### User Story US-ST02 — Preferencias de negocio sincronizadas (Priority: P1)

Como **Usuario Registrado**, quiero **guardar preferencias de cuenta en el servidor**, para **consistencia entre sesiones y dispositivos**.

**Why this priority**: Materializa M-10A; extiende 001 CU-04 con UX explícita.

**Independent Test**: Toggle `recommendations_enabled` off; PATCH API; GET perfil confirma; reload settings muestra estado.

**Acceptance Scenarios**:

1. **Given** settings, **When** modifica dark_mode, audio_quality, recommendations_enabled, privacy_public, **Then** PATCH `/users/me/preferences` con campos válidos (001 RB-010).
2. **Given** PATCH exitoso, **When** consulta perfil, **Then** valores reflejados en GET `/users/me`.
3. **Given** PATCH parcial, **When** solo envía un campo, **Then** demás prefs sin cambio (001 FR-011).
4. **Given** PATCH inválido, **When** API rechaza, **Then** UI muestra error claro; estado previo preservado.
5. **Given** conflicto tema UI vs dark_mode backend, **When** perfil carga, **Then** RB-ST05 define precedencia (plan).

**Maps to**: CU-ST03 | FR-ST05–FR-ST08 | M-10A

---

### User Story US-ST03 — Toggles UI locales (Priority: P2)

Como **Usuario Registrado**, quiero **configurar visibilidad de KPIs en dashboard**, para **personalizar densidad de información**.

**Acceptance Scenarios**:

1. **Given** toggle KPI en settings, **When** activa/desactiva, **Then** UiPreferences persiste local.
2. **Given** KPI toggled off, **When** navega Home (004), **Then** KPI oculto según pref local.

**Maps to**: CU-ST04 | FR-ST07

---

### User Story US-ST04 — Transparencia sistema (Priority: P2)

Como **Usuario Registrado**, quiero **ver health del API en settings**, para **confiar en disponibilidad del servicio**.

**Acceptance Scenarios**:

1. **Given** tab api en settings, **When** fetch `/health`, **Then** muestra status, table count, duckdb version.
2. **Given** health error, **When** tab carga, **Then** mensaje error sin stack trace ni paths internos (RB-ST06).
3. **Given** health OK, **When** renderiza, **Then** no expone credentials ni connection strings.

**Maps to**: CU-ST05 | FR-ST09, FR-ST10

---

### User Story US-ST05 — Settings engineer (Priority: P3)

Como **Usuario Engineer**, quiero **ver tabs warehouse y pipeline en settings**, para **acceso rápido al estado de datos**.

**Acceptance Scenarios**:

1. **Given** usuario con rol engineer (001 US-07), **When** abre settings, **Then** tabs warehouse y pipeline visibles.
2. **Given** usuario estándar, **When** abre settings, **Then** tabs warehouse/pipeline ocultas.
3. **Given** engineer en tab warehouse, **When** carga, **Then** información estado warehouse sin mutación.

**Maps to**: CU-ST06 | FR-ST11 — *rol definido 001 RB-015*

---

### Edge Cases

- PATCH preferences offline: error message; no silent fail.
- Perfil API timeout: skeleton + retry; no datos stale de otro user.
- Engineer role revoked mid-session: tabs ocultas en próxima navegación settings.
- Usuario sin playlists: preview vacío con empty state.
- health endpoint 503: degraded message en tab api.

---

## Requirements *(mandatory)*

### Functional Requirements — Perfil UI

- **FR-PF01**: UI MUST provide authenticated route `/users` profile screen.
- **FR-PF02**: MUST fetch profile from GET `/users/me` on load (001 contract).
- **FR-PF03**: MUST display identity fields: username, email, plan, favorite_genre, preferences summary — MUST NOT display password or hash.
- **FR-PF04**: MUST display library stats: favorites_count, playlists_count from API response.
- **FR-PF05**: MUST display playlist preview (max 6 items) when provided by API.

### Functional Requirements — Settings

- **FR-ST01**: UI MUST provide authenticated route `/settings` with tabbed interface.
- **FR-ST02**: MUST support theme selection: dark, light, system via UiPreferencesService.
- **FR-ST03**: MUST support language selection ES/EN via I18nService.
- **FR-ST04**: MUST persist UI preferences (theme, language, KPI toggles) locally across browser sessions.
- **FR-ST05**: MUST allow update of business preferences via PATCH `/users/me/preferences` for fields: dark_mode, audio_quality, recommendations_enabled, privacy_public, favorite_genre (per 001 RB-010).
- **FR-ST06**: MUST map each UI control to explicit API preference key — documented in plan.
- **FR-ST07**: MUST provide KPI display toggles stored in local UiPreferences only.
- **FR-ST08**: MUST show save confirmation or error feedback on API preference update.
- **FR-ST09**: MUST fetch and display GET `/health` on api settings tab.
- **FR-ST10**: MUST show loading and error states on health fetch without exposing internals.
- **FR-ST11**: MUST show warehouse and pipeline settings tabs ONLY for users with engineer role (001 RB-015).
- **FR-ST12**: MUST require authentication for all settings routes (001 guards).

### Non-Functional Requirements

- **NFR-01**: Theme and language change MUST apply within ≤ 1s perceived (M-10B).
- **NFR-02**: Profile load MUST complete ≤ 2s p95.
- **NFR-03**: MUST NOT store secrets, tokens, or passwords in UI preferences local storage beyond session mechanism of 001.
- **NFR-04**: Settings strings MUST be i18n-complete ES/EN (TA-11).
- **NFR-05**: Health display MUST comply §18 — no credentials, internal paths, or PII of other users.

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-ST01** | Business preferences authoritative store: backend `preferences_json` (001 RB-010). |
| **RB-ST02** | UI-only preferences (KPI toggles) MAY remain local-only — MUST be documented in plan. |
| **RB-ST03** | `dark_mode` backend preference and UI theme SHOULD synchronize — sync strategy defined in plan. |
| **RB-ST04** | `privacy_public` MUST default false at registration (001); UI MUST reflect current value. |
| **RB-ST05** | On conflict between UI local theme and API dark_mode on profile load, API value wins unless user explicitly overrides in session (plan details). |
| **RB-ST06** | Health display MUST NOT expose credentials, connection strings, or filesystem paths. |
| **RB-PF01** | Profile UI MUST NOT duplicate login/register/logout flows (001 exclusive). |
| **RB-PF02** | Profile stats MUST derive from backend aggregation — UI MUST NOT compute counts independently of API. |
| **RB-ST07** | `recommendations_enabled=false` MUST affect recommendations UX (005) — disable or show message per plan integration. |

### Key Entities

- **UserProfileView**: UI presentation of 001 UserProfile — username, email, plan, favorite_genre, preferences, stats, playlistPreview[].
- **UiPreferences**: theme (dark|light|system), language (es|en), kpiToggles{}, loadMode — local persistence.
- **BusinessPreferences**: dark_mode, audio_quality, recommendations_enabled, privacy_public, favorite_genre — API authoritative.
- **HealthView**: status, tablesCount, duckdbVersion, timestamp — read-only display model.
- **SettingsTab**: id (general|api|warehouse|pipeline), visible, contentType.

---

## Criterios de Aceptación Globales (Feature)

- **CA-001**: `/users` muestra perfil API completo sin campos sensibles.
- **CA-002**: Stats favorites_count/playlists_count coherentes con biblioteca 002.
- **CA-003**: `/settings` tema/idioma operativos y persistentes localmente.
- **CA-004**: PATCH preferences válidos persisten verificables en GET `/users/me`.
- **CA-005**: Tab api health funcional con estados loading/error.
- **CA-006**: Engineer tabs gated; ocultas para usuario estándar.
- **CA-007**: Zero overlap login/register/logout en pantallas 006.
- **CA-008**: Trazabilidad matriz OE→HU completa.

---

## Success Criteria *(mandatory)*

- **SC-001**: 90% usuarios cambian tema o idioma exitosamente en primer intento.
- **SC-002**: 100% PATCH preferences válidos persisten — verificables en GET `/users/me` post-save.
- **SC-003**: 95% profile page loads ≤ 2s p95.
- **SC-004**: 0 instancias password/hash en DOM profile view (auditoría).
- **SC-005**: 100% usuarios estándar no ven tabs warehouse/pipeline.

---

## Riesgos

| ID | Riesgo | Prob. | Impacto | Mitigación |
|----|--------|-------|---------|------------|
| R-001 | Duplicidad funcional con 001 | Media | Alto | Delimitation table; RB-PF01 |
| R-002 | Dual store prefs drift (UI vs API) | Alta | Medio | RB-ST03, RB-ST05; plan sync |
| R-003 | Settings expone información técnica excesiva | Baja | Medio | RB-ST06, NFR-05 |
| R-004 | Engineer gating diverge 001/006 | Baja | Alto | Single source 001 RB-015 |
| R-005 | recommendations_enabled desync con 005 | Media | Medio | RB-ST07 integration plan |

---

## Dependencias

| Dependencia | Tipo | Referencia |
|-------------|------|------------|
| Identidad y acceso | Hard | `001-user-identity-access` |
| Biblioteca personal | Soft | `002-personal-music-library` (stats counts) |
| Descubrimiento personalizado | Soft | `005-personalized-discovery` (recommendations_enabled) |
| Experiencia escucha | Soft | `004-listening-experience` (KPI toggles Home) |
| Data ops / ELT | Soft | Tab pipeline content (008 future) |

---

## Relación con Constitución v1.0.0

| Sección | Aplicación |
|---------|------------|
| TA-11 i18n ES/EN | FR-ST03, NFR-04 |
| TA-12 Design system | FR-ST02 theme |
| §5 P9 Contract-first | Consume 001 API; no redefine |
| §12 Trazabilidad | Matriz completa |
| §18 Seguridad UI | NFR-03, RB-ST06, FR-PF03 |
| §4.3 Operativo | OO-10, OO-11 |

---

## Out of Scope

- Cambio de password / verificación email
- Eliminación cuenta GDPR / export datos
- Login / register / logout UI (001)
- Admin user management / impersonation
- Notificaciones push/email preferences
- Edición username/email (v1 read-only identity fields)

---

## Assumptions

- Usuario alcanza settings/profile autenticado vía guards 001.
- API `/users/me` y PATCH preferences estables per spec 001.
- Engineer role detection unchanged from 001 until future RBAC spec.
- Health endpoint disponible en entorno demo.

---

**Next Step**: `/speckit-plan` — run `/speckit-clarify` if prefs sync strategy (RB-ST03/05) requires product decision.
