# Spec 014 — Spec closure

**Feature:** Estabilización del Repositorio y Fundación Package-by-Domain  
**Directory:** `automation/specs/014-repository-stabilization-domain-foundation/`  
**Fecha de cierre documental:** 2026-07-11

---

## Estado final

# CLOSED_WITH_ACCEPTED_DEBT

La spec 014 se cierra documentalmente con evidencia de fases A–G y deudas explícitas en `accepted-debt.md`.  
**No** se inicia la spec 015 en este acto.

---

## Cumplimiento por user story (sin alterar requisitos)

| US | Objetivo | Resultado |
|----|----------|-----------|
| US1 Gobierno / constitución | Alinear monorepo, specs, package-by-domain, audio real, OpenSpec | **Completado** |
| US2 Frontend packages | Absorber `features/` sin cambiar URLs | **Completado** (Playwright **no verificado**) |
| US3 Backend packages + fachada `/api/v1` + auth | Dominios técnicos + seguridad documentada | **Completado** (shims = **diferido**) |
| US4 ELT canónico | Declarar `analytics/elt`; no borrar `app/etl`; row counts | **Completado** (parity total = **diferido**) |
| US5 Playback docs only | Congelar decisión; cero código player | **Completado** (G7 interactivo = **no verificado**) |

---

## Tareas — resumen

### Completadas (implementación / docs / validación)

T003–T012 (A/B, según evidencia de ejecución previa y constitución), T014–T021 (C), T023–T029 (D), T031–T034 (E), T036–T039 (F), T041–T045 (G).

### Parciales

- T039 / CHK035 / G13: pruebas automatizadas OK; smoke interactivo no.
- Build FE: PASS con posibles warnings de budget.
- CHK046: reproducción parcial.

### Diferidas (proceso Git / retiro futuro)

- T001/T002/T005/T013/T022/T030/T035/T040/T046 — commits y rama gestionados por el usuario.
- Retiro de shims, `app/etl`, API legacy, playback-core migration — specs futuras.
- Reescritura fila-a-fila TRACEABILITY-MASTER.

### No verificadas

- Docker Compose end-to-end.
- Playwright e2e.
- Login SPA en browser (CHK041).
- CI remoto en GitHub Actions.
- `git status` por el agente (prohibido).

### Fuera de alcance (no fallos)

Ver `spec.md` § Fuera de alcance y `accepted-debt.md`.

---

## Artefactos de evidencia

| Archivo | Rol |
|---------|-----|
| `evidence/closure-report.md` | Informe Phase G |
| `evidence/final-validation.md` | Consolidación de gates/pruebas |
| `evidence/accepted-debt.md` | Deudas aceptadas |
| `evidence/spec-closure.md` | Este documento |
| `docs/playback/SPEC_014_PHASE_F_DECISION.md` | Decisión playback |
| `docs/architecture/elt.md` | ELT canónico |

---

## Trazabilidad

- Specs 001–013 **no** movidas.
- TRACEABILITY-MASTER: cabecera con mapeo `backend/`→`apps/backend/`, `users`→`identity`, etc. (Spec 014 G).
- **No** se afirman funciones empresariales (CRM, billing, orgs) como implementadas.

---

## Condiciones de reapertura

Reabrir o crear follow-up si:

- se retiran shims sin verificar consumidores;
- se cambia el esquema DuckDB sin spec;
- se presenta playback-core o Docker/Playwright como validados sin nueva evidencia;
- se inicia trabajo de dominios empresariales sin spec dedicada.

---

## Firma documental

| Campo | Valor |
|-------|-------|
| Cierre | CLOSED_WITH_ACCEPTED_DEBT |
| Spec 015 | **No iniciada** |
| Commits | Manuales (usuario) |
