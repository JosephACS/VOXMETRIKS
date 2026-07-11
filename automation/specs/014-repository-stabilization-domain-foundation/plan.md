# Implementation Plan: Estabilización del Repositorio y Fundación Package-by-Domain

**Branch**: `014-repository-stabilization-domain-foundation` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Status**: **CLOSED_WITH_ACCEPTED_DEBT** (2026-07-11) — ejecución A–G completada; deudas en `evidence/accepted-debt.md`

## Summary

Consolidar package-by-domain técnico (`identity`, `catalog`, `engagement`, `analytics`, `ai`) sobre el monorepo existente, con **fachada `/api/v1`** que conserve contratos del frontend, dual ELT declarado (canónico `analytics/elt` sin borrar `app/etl`), y playback **solo documentado**.

**Sin cambios funcionales intencionales**, excepto **seguridad documentada** (proteger endpoints sensibles públicos).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Angular 21 (frontend)

**Primary Dependencies**: FastAPI, DuckDB, Angular, Spec Kit (`.specify` + `automation/specs`)

**Storage**: DuckDB `data/warehouse/` — **esquema inmutable en 014**; row counts de tablas críticas como gate

**Testing**: pytest, Vitest, build, lint, Playwright según disponibilidad; gates G1–G9 (spec)

**Target Platform**: Dev local Windows + Docker compose (`workers: 1`)

**Project Type**: Monorepo web

**Constraints**:
- No romper rutas FE ni contratos `/api/v1` consumidos
- No declarar Packages V1 como “toda la API canónica”
- No mover specs 001–013; no crear dominios empresariales vacíos
- No modificar código del player; no integrar `playback-core` en 014
- No eliminar `apps/backend/app/etl`; adaptador ELT solo con paridad demostrable
- Commits pequeños; rollback por commit; stop on unresolvable regression
- No stash/reset/commit de trabajo ajeno sin autorización
- No versionar secretos ni archivos generados

**Scale/Scope**: Estabilización estructural

**Principio**: negocio → objetivos → procesos → actores → casos de uso → reglas → datos → backend → frontend → reportes → IA

## Constitution Check

| Gate | Expectativa |
|------|-------------|
| §13 Organización monorepo | Mantener raíz; enmienda solo desfaces |
| Package-by-domain | Packages técnicos; no dominios vacíos |
| §16 Implementación | Sin cambio funcional intencional salvo seguridad documentada |
| Specs en `automation/specs/` | Conservar ubicación |
| OpenSpec / Spec Kit | Spec 014 antes de fases C–G |

## Phased Execution (autorizada por el usuario)

| Fase | Nombre | Entregable clave | Stop condition |
|------|--------|------------------|----------------|
| **A** | Baseline | Rama; `git status` limpio o solo 014; resumen tests | Cambios ajenos sin autorización; proyecto ya roto |
| **B** | Constitución | Enmienda puntual | — |
| **C** | Frontend | `features/` → `packages/`; rutas iguales | Fallo gates FE / login |
| **D** | Backend | packages + fachada `/api/v1` + auth sensible | Regresión contrato / pytest / 401-403 |
| **E** | ELT | Declarar `analytics/elt` canónico; row counts | Delta injustificado; esquema cambiado |
| **F** | Playback | Solo docs de dirección futura + tests existentes | Cualquier diff de código player |
| **G** | Limpieza | Legacy sin consumidores; docs/CI | Consumidor residual; secretos en git |

## Target Layout (post-014, gradual)

### Backend

```text
apps/backend/app/
├── core/
├── platform/
├── packages/
│   ├── identity/
│   ├── catalog/
│   ├── engagement/
│   ├── analytics/
│   └── ai/
└── api/               # fachada /api/v1 + adaptadores enterprise/v2
```

### Frontend

```text
apps/frontend/src/app/
├── core/
├── shell/
├── packages/
│   ├── identity/
│   ├── catalog/
│   ├── engagement/
│   ├── analytics/
│   ├── data-engineering/
│   ├── administration/
│   ├── smart/
│   └── ai/
└── shared/
```

Playback: **sin cambios de código en 014**. `MusicPlayerService` se mantiene. Dirección futura: SoT = `playback-core` (spec posterior).

## Compatibility Strategy

| Superficie | Estrategia |
|------------|------------|
| FE routes | Paths inmutables; solo imports |
| Fachada `/api/v1` | Conserva contratos FE; implementación por endpoint según consumidores, pruebas y seguridad |
| Enterprise V1 / V2 | Adaptadores mientras haya consumidores; auth en D |
| Dual ELT | Declarar `analytics/elt` canónico; **conservar** `app/etl`; adaptador solo con paridad; `RUN_ETL_ON_BOOT` intacto |
| Playback | Solo documentación; cero integración de código |

## Tablas críticas (row counts Fase E)

Confirmadas en código: `dim_track`, `dim_artista`, `dim_album`, `fact_streaming`, `app_user`, `app_session`, `app_playlist`, `app_favorite`.

## Project Structure (this feature)

```text
automation/specs/014-repository-stabilization-domain-foundation/
├── spec.md
├── plan.md
├── tasks.md
└── checklist.md
```

## Validation per Phase

Gates G1–G9 (ver spec) + lo disponible:

- Backend inicia (G1); pytest
- Frontend carga + login (G2); lint/test/build; Playwright si hay
- Contratos FE (G3); 401/403 en sensibles (G4)
- Esquema DuckDB (G5); row counts (G6)
- Reproducción básica (G7) — smoke, sin tocar código player
- Sin secretos/generados (G8); rollback por commit (G9)

No inventar resultados.

## Risks (referenciados)

Auth enterprise/v2; dual ELT sin paridad; player fuera de alcance 014 — auditoría 2026-07-11 y OMEGA.

## Next Step After Approval

1. Autorización explícita del usuario  
2. Fase A según [tasks.md](./tasks.md) (incl. `git status` estricto)
