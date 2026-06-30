# Implementation Plan: Calidad Automática y Tests de Hotspots

**Branch**: `012-auto-quality-gates` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Status**: Implemented

## Summary

Establecer gates de calidad repetibles en backend (Ruff + pytest) y frontend (Angular ESLint + Vitest), con scripts `check` unificados y tests focalizados en cuatro hotspots de alto riesgo. Vitest es el estándar único frontend (Angular 21); Karma/Jasmine no se adoptan.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.9 / Angular 21 (frontend)

**Primary Dependencies**: FastAPI, DuckDB, pytest, ruff; Angular 21, vitest, jsdom, angular-eslint, eslint

**Storage**: DuckDB (tests hotspot usan `:memory:` aislado)

**Testing**: pytest 8.x (backend), Vitest 4.x vía `ng test --no-watch` (frontend)

**Target Platform**: Windows dev + CI genérico (PowerShell/Makefile, npm scripts)

**Project Type**: Web application (monorepo `backend/` + `frontend/`)

**Performance Goals**: `make check` / `npm run check` < 2 min en dev

**Constraints**: NO modificar lógica de negocio; auto-fixes mecánicos permitidos; lint calibrado para legacy

**Scale/Scope**: ~15 archivos nuevos/modificados de tooling + 2 archivos de test hotspot

## Constitution Check

*GATE: Passed — aligns with Constitution §9 Estrategia de Calidad y §10 Estrategia de Testing*

| Principle | Compliance |
|-----------|------------|
| §9 Calidad automática | Ruff + ESLint + scripts `check` |
| §10 Testing | pytest suite + Vitest; hotspots cubiertos |
| §16 Implementación | Sin cambios de comportamiento en hotspots |
| §12 Trazabilidad | Spec 012 + tasks + evidencia en código |

## Project Structure

### Documentation (this feature)

```text
specs/012-auto-quality-gates/
├── spec.md
├── plan.md              # This file
├── research.md
├── quickstart.md
├── tasks.md
├── checklists/requirements.md
└── traceability-appendix.md
```

### Source Code (delivered)

```text
backend/
├── pyproject.toml           # Ruff + pytest config
├── Makefile                 # lint, test, check
├── requirements.txt         # ruff, pytest-cov
└── tests/
    └── test_quality_hotspots.py

frontend/
├── eslint.config.js
├── vitest.config.ts
├── angular.json             # runnerConfig, budget tweak
├── package.json             # lint, test, check scripts
└── src/
    ├── test-setup.ts
    └── app/shared/services/
        └── music-player.service.spec.ts
```

## Architecture Decisions

### AD-01: Vitest como estándar frontend

**Decision**: Vitest único; `ng test --no-watch --no-progress` para CI.  
**Rationale**: Angular 21 default builder; `tsconfig.spec.json` ya declara `vitest/globals`.  
**Alternatives rejected**: Karma (no instalado), Jasmine standalone (redundante).

### AD-02: Ruff sin reglas UP (pyupgrade)

**Decision**: `select = ["E","W","F","I","B","C4","SIM"]` — sin `UP`.  
**Rationale**: ~470 hallazgos de modernización de tipos reescribirían todo el backend.  
**Follow-up**: Pasada dedicada `UP` en spec futura.

### AD-03: ESLint pragmático para legacy

**Decision**: Desactivar `prefer-inject`, template a11y estricta; `max-warnings 50`.  
**Rationale**: 99+ errores en código preexistente; gate útil sin bloquear merge.

### AD-04: Tests hotspot aislados

**Decision**: DuckDB `:memory:` en pytest; mocks de servicios en Vitest.  
**Rationale**: Sin FastAPI TestClient ni red; respeta "no modificar lógica".

## Validation Evidence (2026-06-29)

| Command | Result |
|---------|--------|
| `python -m ruff check .` (backend) | All checks passed |
| `python -m pytest -q` (backend) | 74 passed |
| `npm run lint` (frontend) | 0 errors, 11 warnings |
| `npm run test` (frontend) | 8 passed |
| `npm run build` (frontend) | OK → `dist/app` |

**Coverage**: backend total 65%; `tracks/list.py` 100%; `recommendations/service.py` 77%; `synthetic/generator.py` 49% (guards).

## Phase 0: Research

Ver [research.md](./research.md).

## Phase 1: Design Artifacts

Ver [quickstart.md](./quickstart.md) para comandos operativos.

## Phase 2: Tasks

Ver [tasks.md](./tasks.md) — todas completadas; converged.
