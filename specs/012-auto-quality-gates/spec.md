# Feature Specification: Calidad Automática y Tests de Hotspots

**Feature Branch**: `012-auto-quality-gates`  
**Feature Directory**: `specs/012-auto-quality-gates/`  
**Created**: 2026-06-29  
**Status**: Implemented — converged via `/speckit-converge`  
**Input**: Preparar VOXMETRIKS_V2 para mantenimiento a largo plazo: Ruff (backend), Angular ESLint (frontend), scripts `lint` / `lint:fix` / `test` / `build` / `check`, estándar único de testing (Vitest), y tests de hotspots sin modificar lógica de negocio.

**Prerrequisitos:** Constitución §9 (Estrategia de Calidad) y §10 (Estrategia de Testing); specs 001–011 como base funcional.

**Evidencia base:** `backend/pyproject.toml`, `backend/Makefile`, `backend/tests/test_quality_hotspots.py`, `frontend/eslint.config.js`, `frontend/vitest.config.ts`, `frontend/src/test-setup.ts`, `frontend/src/app/shared/services/music-player.service.spec.ts`.

---

## Contexto Empresarial

Voxmetriks evoluciona hacia professionalización (Constitución §1). Sin gates automáticos de calidad ni cobertura mínima en rutas críticas, cada cambio en warehouse, catálogo o reproductor aumenta el riesgo de regresiones silenciosas.

Esta spec formaliza la **capa de mantenibilidad**: herramientas de lint, scripts unificados, un solo runner de tests frontend, y pruebas focalizadas en hotspots de alto impacto — **sin alterar comportamiento de producción**.

---

## Problema

### Situación actual (pre-spec)

- Backend sin Ruff configurado de forma centralizada.
- Frontend sin ESLint; `ng test` sin modo CI documentado.
- Coexistencia potencial Vitest / Karma / Jasmine sin decisión explícita.
- Hotspots críticos sin tests dedicados:
  - `generate_synthetic_activity`
  - `get_tracks_cursor`
  - `get_recommendations`
  - `MusicPlayerService.loadTrack`

### Problema de negocio

**El equipo no puede validar cambios de forma repetible** antes de merge o release, ni detectar regresiones en las rutas de datos y reproducción más sensibles.

---

## Objetivo

Gobernar la **capacidad de Calidad Automática y Tests de Hotspots**:

1. Configurar lint/format backend (Ruff) y frontend (Angular ESLint).
2. Exponer scripts homogéneos `lint`, `lint:fix`, `test`, `build`, `check`.
3. Estandarizar testing frontend en **Vitest** (Angular 21 `@angular/build:unit-test`).
4. Añadir tests de hotspots backend y frontend **sin modificar lógica**.
5. Validar que todos los comandos ejecutan correctamente en CI/local.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Desarrollador ejecuta gate de calidad backend (Priority: P1)

Como desarrollador backend, quiero ejecutar un único comando que valide lint y tests para saber si mi cambio es mergeable.

**Why this priority**: Bloquea regresiones en API y warehouse — núcleo del producto.

**Independent Test**: `cd backend && make check` termina con exit code 0.

**Acceptance Scenarios**:

1. **Given** el repo con dependencias instaladas, **When** ejecuto `make lint`, **Then** Ruff reporta sin errores bloqueantes.
2. **Given** la suite pytest, **When** ejecuto `make test`, **Then** todos los tests pasan incluyendo `test_quality_hotspots.py`.
3. **Given** cambios solo mecánicos de estilo, **When** ejecuto `make lint-fix`, **Then** se aplican auto-fixes sin tocar lógica de negocio.

---

### User Story 2 - Desarrollador ejecuta gate de calidad frontend (Priority: P1)

Como desarrollador frontend, quiero lint + tests + build en un comando para validar la SPA antes de PR.

**Why this priority**: Angular 21 ya usa Vitest; falta formalizar ESLint y scripts CI.

**Independent Test**: `cd frontend && npm run check` termina con exit code 0.

**Acceptance Scenarios**:

1. **Given** ESLint configurado, **When** ejecuto `npm run lint`, **Then** no hay errores (warnings acotados permitidos).
2. **Given** Vitest + jsdom setup, **When** ejecuto `npm run test`, **Then** pasan `app.spec.ts` y `music-player.service.spec.ts`.
3. **Given** configuración production, **When** ejecuto `npm run build`, **Then** el bundle se genera en `dist/app`.

---

### User Story 3 - Mantenedor confía en tests de hotspots (Priority: P2)

Como mantenedor, quiero tests que cubran las funciones de mayor riesgo sin reescribir el sistema.

**Why this priority**: ROI máximo — poca superficie, alto impacto.

**Independent Test**: Ejecutar pytest y vitest filtrando archivos hotspot; todos green.

**Acceptance Scenarios**:

1. **Given** DuckDB en memoria con catálogo mínimo, **When** llamo `get_tracks_cursor`, **Then** paginación keyset y búsqueda funcionan según contrato actual.
2. **Given** agregados o fallback, **When** llamo `get_recommendations`, **Then** devuelve `for_you` ordenado y prioriza género favorito.
3. **Given** guards de `generate_synthetic_activity`, **When** faltan parámetros o catálogo, **Then** lanza `ValueError` esperado.
4. **Given** `MusicPlayerService` con mocks, **When** `playTrack` dispara `loadTrack`, **Then** persiste sesión, historial y resuelve YouTube/demo.

---

### Edge Cases

- Ruff en código legacy: reglas `UP` (pyupgrade) excluidas para evitar churn masivo; deuda documentada en `pyproject.toml`.
- ESLint en templates legacy: reglas a11y/`prefer-inject` desactivadas; activación incremental futura.
- jsdom sin `matchMedia` / `localStorage`: polyfills en `src/test-setup.ts`.
- `generate_synthetic_activity` generación completa requiere esquema warehouse extendido — tests cubren guards y partición, no E2E de millones de filas.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-QG01**: Backend MUST configurar Ruff en `backend/pyproject.toml` con reglas de alto valor (E, W, F, I, B, C4, SIM).
- **FR-QG02**: Backend MUST exponer `make lint`, `make lint-fix`, `make test`, `make build`, `make check` vía `backend/Makefile`.
- **FR-QG03**: Backend MUST incluir `ruff` y `pytest-cov` en `requirements.txt`.
- **FR-QG04**: Frontend MUST configurar Angular ESLint flat config en `frontend/eslint.config.js`.
- **FR-QG05**: Frontend MUST exponer `lint`, `lint:fix`, `test`, `build`, `check` en `package.json`.
- **FR-QG06**: Frontend MUST usar **Vitest** como único estándar (`ng test --no-watch`); Karma/Jasmine NO son estándar del proyecto.
- **FR-QG07**: Backend MUST tener `backend/tests/test_quality_hotspots.py` cubriendo `generate_synthetic_activity`, `get_tracks_cursor`, `get_recommendations`.
- **FR-QG08**: Frontend MUST tener `music-player.service.spec.ts` cubriendo comportamiento observable de `loadTrack` vía `playTrack`.
- **FR-QG09**: Implementación MUST NOT modificar lógica de negocio de los hotspots — solo configuración, tests y auto-fixes mecánicos.
- **FR-QG10**: `npm run check` y `make check` MUST ejecutar sin error en el estado entregado.

### Key Entities

- **Quality Gate Script**: Comando unificado (`check`) que encadena lint → test → build.
- **Hotspot Test Suite**: Conjunto acotado de pruebas sobre funciones de alto riesgo.
- **Lint Profile**: Conjunto de reglas Ruff/ESLint calibrado para codebase legacy.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-QG01**: `make check` (backend) completa en < 2 min en entorno dev estándar con exit 0.
- **SC-QG02**: `npm run check` (frontend) completa con exit 0 (lint 0 errors, tests green, build OK).
- **SC-QG03**: Suite backend ≥ 70 tests pasando; suite hotspot ≥ 13 casos.
- **SC-QG04**: Suite frontend ≥ 8 tests Vitest pasando.
- **SC-QG05**: Cobertura backend total ≥ 60% (`pytest --cov=app`); `tracks/list.py` hotspot al 100%.
- **SC-QG06**: Documentación SDD completa: `spec.md`, `plan.md`, `tasks.md`, checklist en `specs/012-auto-quality-gates/`.

---

## Assumptions

- Python 3.12 y Node 20+ disponibles en dev/CI.
- Angular CLI 21.x con builder `@angular/build:unit-test` ya presente.
- Deuda preexistente (`mutations.py` typo `id_genre`) se documenta, no se corrige en esta spec (no modificar lógica).
- Budget CSS `home.component` ajustado mínimamente (16→17 kB) solo para que `build` pase — sin cambio visual.

---

## Delimitación

| In scope | Out of scope |
|----------|--------------|
| Ruff, ESLint, Vitest, scripts check | Migración masiva pyupgrade (UP rules) |
| Tests hotspots listados | Cobertura 100% del monorepo |
| Polyfills test jsdom | E2E Playwright/Cypress |
| Documentación Spec Kit 012 | Refactor HomeComponent / player |
