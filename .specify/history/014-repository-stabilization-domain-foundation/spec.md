> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Estabilización del Repositorio y Fundación Package-by-Domain

**Feature Branch**: `014-repository-stabilization-domain-foundation`  
**Feature Directory**: `.specify/history/014-repository-stabilization-domain-foundation/`  
**Created**: 2026-07-11  
**Status**: **CLOSED_WITH_ACCEPTED_DEBT** (cierre documental 2026-07-11) — ver `evidence/spec-closure.md`  
**Input**: Estabilizar la arquitectura actual de VOXMETRIKS y consolidar package-by-domain sin cambiar el comportamiento funcional ni crear todavía los nuevos módulos empresariales.

**Prerrequisitos:** Constitución v1.0.0; specs 001–013; auditoría de dominio (sesión 2026-07-11, no versionada aún en `.specify/reviews/`).

**Número de spec:** **014** (siguiente disponible tras 013-academic-defense-deliverables).

---

## Contexto

VOXMETRIKS ya opera como monorepo (`apps/`, `analytics/`, `automation/`, `infrastructure/`). El package-by-domain parcial (`streaming`, `analytics`, `users`) coexiste con:

- Triple superficie API (`/api/v1` enterprise + packages + `/api/v2`)
- Dual ELT (`analytics/elt` + `apps/backend/app/etl`)
- Duplicación FE `features/` vs `packages/`
- Playback con dos capas (`MusicPlayerService` + `playback-core`)

Esta spec **no** introduce CRM, billing, organizations ni otros dominios empresariales vacíos. Solo estabiliza y consolida lo existente.

---

## Objetivo

> Estabilizar la arquitectura actual y consolidar package-by-domain **sin cambios funcionales intencionales**, excepto **cambios de seguridad documentados** (p. ej. proteger endpoints sensibles actualmente públicos). Mantener adaptadores de compatibilidad hasta validar paridad.

---

## Principio de diseño

Orden obligatorio de razonamiento y documentación:

> **negocio → objetivos → procesos → actores → casos de uso → reglas → datos → backend → frontend → reportes → IA**

---

## Fuera de alcance

- Crear dominios: organizations, crm, subscriptions, billing, campaigns, customer-success, support, compliance, catalog-rights
- Modificar código del reproductor o integrar gradualmente `playback-core` en 014
- Eliminar `apps/backend/app/etl` o cambiar esquema DuckDB
- Mover `automation/specs` dentro de `.specify`
- Eliminar rutas legacy sin consumidores verificados
- Multi-tenant, Redis obligatorio, o escala “millones de usuarios”

---

## Tablas críticas de referencia (nombres confirmados en código)

| Tabla | Evidencia |
|-------|-----------|
| `dim_track` | `analytics/elt/pipelines/elt_pipeline.py`, smart/queries |
| `dim_artista` | idem |
| `dim_album` | `elt_pipeline.py` (`_build_dim_album`) |
| `fact_streaming` | gold/smart/services |
| `app_user` | `app_storage.py`, auth/session flows |
| `app_session` | auth/session (UUID en sesión; ver OMEGA) |
| `app_playlist` | `app_storage.py`, `playlist_service.py` |
| `app_favorite` | `app_storage.py`, `favorite_service.py` |

Estas tablas son la base de comparación de **row counts** en Fase E y gates de warehouse. No se altera su esquema en 014.

---

## User Scenarios & Testing

### User Story 1 — Gobierno alineado con el monorepo real (Priority: P1)

Como mantenedor, necesito que la Constitución y Spec Kit describan la estructura real y las reglas de migración, para que ningún cambio futuro cree módulos vacíos ni rompa el gobierno OpenSpec.

**Why this priority**: Sin gobierno correcto, la consolidación de código contradice la autoridad del proyecto.

**Independent Test**: Leer Constitución actualizada y verificar monorepo, `.specify/history/`, package-by-domain técnico vs empresarial, audio real, principio de diseño completo, y prohibición de módulos vacíos.

**Acceptance Scenarios**:

1. **Given** Constitución previa con desfaces (p. ej. audio WAV-only), **When** se aplica Fase B, **Then** refleja monorepo, specs en `.specify/history/`, audio según código real (YouTube + fallback Audius + demo), naming honesto AI/Enterprise/RC, y el principio negocio→…→IA.
2. **Given** un intento de crear carpeta empresarial vacía, **When** se consulta la Constitución, **Then** está prohibido sin spec dedicada.

---

### User Story 2 — Frontend consolidado sin romper rutas (Priority: P1)

Como usuario de la SPA, sigo usando las mismas URLs (`/discover`, `/dashboard`, `/insights/*`, `/tracks`, etc.) tras absorber `features/` en `packages/`.

**Why this priority**: Regresión de navegación rompe demo y E2E.

**Independent Test**: `npm run build`, `npm run test`, `npm run lint`; rutas de `app.routes.ts` sin cambio de path; E2E disponibles; frontend carga y permite login.

**Acceptance Scenarios**:

1. **Given** rutas actuales en `app.routes.ts`, **When** se consolida `features/dashboard|analytics|tracks`, **Then** los paths públicos no cambian.
2. **Given** build/lint/unit verdes (o fallos documentados preexistentes), **When** termina Fase C, **Then** no hay regresión nueva atribuible a la consolidación.

---

### User Story 3 — Backend package-by-domain con fachada `/api/v1` estable (Priority: P1)

Como consumidor de `/api/v1`, las mismas operaciones usadas por el frontend siguen funcionando. Existe una **fachada canónica bajo `/api/v1`** que conserva esos contratos; la implementación detrás de cada endpoint se elige por **consumidores, pruebas y seguridad** — **no** se declara automáticamente “Packages V1 = toda la API canónica”.

**Why this priority**: El FE y demos dependen de contratos HTTP actuales.

**Independent Test**: pytest; smoke de endpoints consumidos; auth en rutas sensibles → 401/403 sin permiso; backend inicia.

**Acceptance Scenarios**:

1. **Given** FE usando `environment.apiUrl` → `/api/v1`, **When** se reorganizan packages, **Then** los contratos consumidos se mantienen vía fachada (origen enterprise o packages según evidencia).
2. **Given** rutas sensibles hoy públicas, **When** Fase D aplica auth documentada, **Then** responden 401/403 sin permiso y los flujos autenticados documentados siguen OK.

---

### User Story 4 — ELT declarado canónico sin borrar el pipeline de boot (Priority: P2)

Como operador, `analytics/elt` se declara pipeline canónico. `apps/backend/app/etl` **no se elimina**. Solo se crea adaptador si hay **paridad demostrable**. Se mantiene `RUN_ETL_ON_BOOT`. Sin cambio de esquema DuckDB. Se comparan row counts de tablas críticas antes/después.

**Independent Test**: row counts de tablas críticas; boot con `RUN_ETL_ON_BOOT`; scripts ELT/warehouse si disponibles.

**Acceptance Scenarios**:

1. **Given** dual ELT, **When** se declara canónico `analytics/elt`, **Then** docs/ops lo reflejan y `app/etl` permanece.
2. **Given** sin paridad demostrable, **When** se evalúa adaptador, **Then** no se fuerza el reemplazo; boot actual se mantiene.
3. **Given** comparación de row counts, **When** hay delta, **Then** se justifica o se detiene/rollback.

---

### User Story 5 — Playback: solo documentar dirección futura (Priority: P2)

Como oyente, la reproducción básica permanece funcional. En 014 **no** se modifica código del player ni se integra `playback-core`. Se documenta la dirección futura (SoT = `playback-core`; `MusicPlayerService` se mantiene). Se ejecutan pruebas existentes.

**Independent Test**: vitest/playback specs existentes; smoke de reproducción básica; cero diff en archivos del player.

**Acceptance Scenarios**:

1. **Given** Fase F, **When** se completa, **Then** solo hay documentación de dirección futura + resultados de tests existentes.
2. **Given** cualquier propuesta de cambiar player, **When** se evalúa en 014, **Then** se rechaza (fuera de alcance).

---

### Edge Cases

- Prueba no disponible → documentar “no ejecutado”, no inventar PASS.
- Regresión no resoluble → detener fase y rollback por commit de etapa.
- Consumidor desconocido de ruta legacy → mantener adaptador; no archivar.
- Cambios ajenos a 014 en working tree → detenerse; no stash/reset/commit sin autorización.

---

## Requirements

### Functional

- **FR-RS01**: Actualizar Constitución solo en secciones necesarias (monorepo, specs path, package-by-domain, audio, módulos vacíos, OpenSpec, naming, principio negocio→…→IA).
- **FR-RS02**: Consolidar FE `features/` → `packages/` manteniendo paths de `app.routes.ts`.
- **FR-RS03**: Backend bajo `packages/{identity,catalog,engagement,analytics,ai}` + `core/` + `platform/` + `api/` con shims/adaptadores.
- **FR-RS04**: Tratar `users` como identity mediante migración compatible (imports/re-exports temporales permitidos).
- **FR-RS05**: Definir **fachada canónica `/api/v1`** que conserve contratos usados por el FE; elegir implementación por endpoint vía consumidores, pruebas y seguridad (no asumir Packages V1 = API canónica completa). Enterprise V1/V2 y demás montajes como adaptadores mientras existan consumidores.
- **FR-RS06**: Auth coherente en rutas sensibles (cambios de seguridad documentados; únicos cambios funcionales intencionales permitidos).
- **FR-RS07**: Declarar `analytics/elt` canónico; **no eliminar** `apps/backend/app/etl`; adaptador solo con paridad demostrable; mantener `RUN_ETL_ON_BOOT`; no cambiar esquema DuckDB; comparar row counts de tablas críticas.
- **FR-RS08**: Playback en 014: documentar dirección futura; **no** modificar código del player; **no** integrar `playback-core`; mantener `MusicPlayerService`; ejecutar pruebas existentes.
- **FR-RS09**: Limpieza solo tras evidencia de cero consumidores; no versionar secretos ni archivos generados.
- **FR-RS10**: Commits pequeños por etapa con rollback por commit; tests/gates tras cada fase; no crear dominios empresariales vacíos.

### Non-Functional

- **NFR-RS01**: Sin cambio intencional de comportamiento UX/API salvo seguridad documentada (FR-RS06).
- **NFR-RS02**: Specs en `.specify/history/`; `.specify` = tooling/gobierno.
- **NFR-RS03**: Cada fase debe poder revertirse con el commit de esa etapa.

---

## Gates de validación (obligatorios por fase, según aplique)

| Gate | Criterio |
|------|----------|
| G1 | Backend inicia |
| G2 | Frontend carga y permite login |
| G3 | Endpoints consumidos por FE mantienen contrato |
| G4 | Rutas sensibles responden 401/403 sin permiso |
| G5 | Esquema DuckDB no cambia |
| G6 | Row counts de tablas críticas se mantienen o se justifican |
| G7 | Reproducción básica permanece funcional |
| G8 | No se versionan secretos ni archivos generados |
| G9 | Cada fase tiene rollback por commit |

---

## Success Criteria

- **SC-RS01**: Spec 014 existe con `spec.md`, `plan.md`, `tasks.md`, `checklist.md`.
- **SC-RS02**: Tras ejecución autorizada, estructura FE/BE converge al layout canónico (o gaps documentados con adaptadores).
- **SC-RS03**: Suites disponibles no introducen fallos nuevos; fallos preexistentes documentados.
- **SC-RS04**: Ningún dominio empresarial vacío creado.
- **SC-RS05**: Fachada `/api/v1` y rutas FE públicas operativas; gates G1–G9 satisfechos o justificados.
- **SC-RS06**: Cero cambios de código de playback en 014; dirección futura documentada.

---

## Trazabilidad

| Artefacto | Relación |
|-----------|----------|
| Specs 001–013 | Base funcional; 014 no las mueve |
| Constitución | Enmienda puntual Fase B |
| Auditoría dominio 2026-07-11 | Input de diseño (no duplicar inventario aquí) |
| OMEGA / PRODUCTION_READINESS | Motivación de auth; fuera de alcance “escala internacional” |
| Audio providers | YouTube + Audius (`audius_provider.py` en `resolver.py`) + demo — evidencia activa |
