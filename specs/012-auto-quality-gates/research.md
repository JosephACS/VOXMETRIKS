# Research: Calidad Automática y Tests de Hotspots

**Feature**: 012-auto-quality-gates  
**Date**: 2026-06-29

## R1: Framework de tests frontend

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Vitest** (Angular 21 unit-test) | Ya en package.json; builder oficial; rápido | Requiere polyfills jsdom | **Selected** |
| Karma + Jasmine | Histórico Angular | No presente; más lento | Rejected |
| Jasmine standalone | Simple | Duplica Vitest | Rejected |

**Evidence**: `frontend/angular.json` → `@angular/build:unit-test`; `tsconfig.spec.json` → `vitest/globals`.

## R2: Linter backend

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Ruff** | Rápido, lint+format, pyproject.toml | Churn en legacy con UP | **Selected** (sin UP) |
| flake8 + black | Clásico | Dos herramientas | Rejected |
| pylint | Exhaustivo | Lento, ruidoso | Rejected |

## R3: Linter frontend

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **angular-eslint v21** | Alineado con Angular 21 | v22 requiere CLI 22 | **Selected** (^21.4) |
| TSLint | — | Deprecated | Rejected |
| Biome | Rápido | Menos reglas Angular template | Rejected |

## R4: Estrategia tests hotspot `generate_synthetic_activity`

Generación E2E requiere tablas `fact_*`, `dim_usuario` extendido, `ctl_carga_dataset`, etc.

**Decision**: Tests de guards (`ValueError`), `split_activity_counts`, límites — sin invocar generación completa en CI.

## R5: Polyfills Vitest/jsdom

**Gaps found**: `window.matchMedia`, `localStorage`, `HTMLMediaElement.play()` retorna `undefined`.

**Decision**: `frontend/src/test-setup.ts` + `vitest.config.ts` referenciado en `angular.json`.

## R6: Deuda documentada (no corregida)

| File | Issue | Action |
|------|-------|--------|
| `mutations.py:125` | `id_genre` undefined (typo) | per-file-ignore F821; spec futura |
| `user_service.py` | unused `favorite_genre` | per-file-ignore |
