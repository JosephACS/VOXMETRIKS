# Implementation Plan: Identity and Organizations

**Branch**: `016-identity-and-organizations` *(propuesta)* | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Status**: **DESIGN_APPROVED** — **IMPLEMENTATION_COMPLETE** · **CLOSED_WITH_ACCEPTED_DEBT** · I0–I6 COMPLETE.

## Summary

Extender identity existente con dominio `organizations` (membresías, invitaciones, RBAC org-scoped, contexto activo, auditoría, compatibilidad sin org). Sin CRM/billing. Persistencia inicial en DuckDB vía esquema `app_*` (aislamiento por aplicación).

**Cierre I6:** `evidence/spec-closure.md` · deudas `evidence/accepted-debt.md`.

## Technical Context

| Campo | Valor |
|-------|-------|
| Language | Python 3.12 / TypeScript (Angular) |
| Backend | FastAPI `packages/identity` + futuro `packages/organizations` |
| Storage | DuckDB `app_*` (**académico**; no SaaS transaccional definitivo) |
| Auth | Bearer session token opaco (existente) — no JWT afirmado |
| Testing | pytest (231) + Angular unit (77) + Playwright **NOT_VERIFIED** (sin specs) |
| Constraints | Constitución 2.0.0; no segundo auth; deny by default |

## Constitution Check

| Gate | Resultado |
|------|-----------|
| Cadena P0 | PASS (docs) |
| No dominios vacíos sin spec | PASS (016 es la spec) |
| DESIGN ≠ implementado | PASS |
| DuckDB límites | PASS (documentado) |
| Audio no es foco | PASS |
| feature.json / Constitución | feature.json **activado a 016 en I0** (permanece en 016 al cierre); Constitución **no** tocada; TRACEABILITY-MASTER **actualizado en I6** |

## Project Structure (futuro — no crear en I0)

```text
apps/backend/app/packages/identity/     # existente — reutilizar
apps/backend/app/packages/organizations/ # NUEVO desde I1
apps/frontend/src/app/packages/organizations/ # NUEVO desde I4
```

## Phases de implementación (autorización 2026-07-11)

Secuencia canónica (renumerada vs borrador histórico I0=schema):

| Fase | Contenido | Estado |
|------|-----------|--------|
| **I0** | Activación tooling + baseline + identity/migración/ownership/compat docs | **COMPLETE** |
| **I1** | Schema `app_organization*` + persistencia + seeds catálogo | **COMPLETE** |
| **I2** | Dominio, reglas y casos de uso | **COMPLETE** |
| **I3** | API, permisos y OrganizationContext | **COMPLETE** |
| **I4** | Frontend y onboarding | NOT STARTED |
| **I5** | Aislamiento, auditoría y compatibilidad | NOT STARTED |
| **I6** | Validación integral y cierre | NOT STARTED |

Detalle: `evidence/i0-implementation-stages.md`.

## Risks

Aislamiento solo en app sobre DuckDB; SHA-256 passwords (deuda seguridad previa); email real diferido (NotificationPort).
