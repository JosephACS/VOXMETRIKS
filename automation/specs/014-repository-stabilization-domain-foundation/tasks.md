# Tasks: Estabilización del Repositorio y Fundación Package-by-Domain

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)  
**Prerequisites**: Autorización explícita del usuario  
**Status**: **CLOSED_WITH_ACCEPTED_DEBT** (cierre documental 2026-07-11) — ver `evidence/spec-closure.md`

## Format: `[ID] [P?] [Story] Description`

**Leyenda de cierre:** `[x]` completado con evidencia · commits = **diferido** (manual usuario) · N/V = no verificado

---

## Phase A: Baseline y respaldo

**Purpose**: Rama limpia + evidencia de salud previa; no tocar trabajo ajeno  
**Resultado cierre:** Completado en ejecución (evidencia de sesión); commits/rama = diferido manual

- [x] T001 Create git branch `014-repository-stabilization-domain-foundation` — **completado** (rama de trabajo 014; commits por usuario)
- [x] T002 `git status` / trabajo ajeno — **completado** en baseline (agente sin Git en fases posteriores por regla usuario)
- [x] T003 Backend pytest baseline — **completado** (suite verde antes/durante 014)
- [x] T004 [P] Frontend test/build/lint baseline — **completado**
- [x] T005 Record baseline — **completado** (notas de fase / warehouse); G8 política anti-secretos

**Checkpoint A**: PASS

---

## Phase B: Constitución y gobierno (US1)

**Purpose**: Enmienda puntual — no reescritura total  
**Resultado cierre:** Completado

- [x] T006 [US1] Constitution: monorepo `apps/` + `analytics/` + `automation/` + `infrastructure/`
- [x] T007 [US1] Specs en `automation/specs/`
- [x] T008 [US1] Package-by-domain técnico vs empresarial; ban empty modules
- [x] T009 [US1] Audio real YouTube + Audius + demo
- [x] T010 [US1] OpenSpec antes de cambios estructurales; naming honesto
- [x] T011 [US1] Principio negocio → … → IA
- [x] T012 [US1] `.specify/feature.json` → 014
- [ ] T013 Commit constitución — **diferido** (manual usuario)

**Checkpoint B**: PASS

---

## Phase C: Frontend consolidation (US2)

**Status**: Completado 2026-07-11

- [x] T014–T021 — ver detalle histórico abajo / checklist C
- [ ] T022 Commit FE — **diferido** (manual usuario)

- [x] T014 [US2] Map `features/dashboard` → `packages/analytics/dashboard/`
- [x] T015 [US2] Map `features/analytics` → `packages/analytics/stream-insights/`
- [x] T016 [US2] Map `features/tracks` → `packages/analytics/top-tracks/`
- [x] T017 [US2] No empty enterprise folders
- [x] T018 [US2] `layouts/` → `shell/` deferred (opcional; **diferido** consciente)
- [x] T019 [US2] Re-exports `features/*.ts` conservados
- [x] T020 [US2] lint/test/build PASS
- [x] T021 [US2] Playwright skipped — **no verificado** / documentado

**Checkpoint C**: PASS (Playwright N/V)

---

## Phase D: Backend consolidation (US3)

### D1 — API facade + authorization — Completado

- [x] T026 [US3][D1] Fachada `/api/v1` + winners
- [x] T027 [US3][D1] Auth 401/403
- [x] T029 [US3][D1] pytest + `/health` (158→ luego 168 en G)

### D2 — Package-by-domain — Completado (shims diferidos para retiro)

- [x] T023 [US3][D2] identity + shim users
- [x] T024 [US3][D2] catalog + engagement + shim streaming
- [x] T025 [US3][D2] analytics/ai montados
- [x] T028 [US3][D2] imports actualizados; shims temporales
- [ ] T030 Commit backend — **diferido** (manual usuario)

**Checkpoint D**: PASS

---

## Phase E: ELT canonical declaration (US4) — Completado

- [x] T031–T034
- [ ] T035 Commit ELT docs — **diferido** (manual usuario)

**Checkpoint E**: PASS (parity total = deuda aceptada)

---

## Phase F: Playback — documentation only (US5) — Completado

- [x] T036–T039
- [ ] T040 Commit playback docs — **diferido** (manual usuario)

**Checkpoint F**: PASS (G7 interactivo N/V)

---

## Phase G: Cleanup — Completado

- [x] T041–T045
- [ ] T046 Commit cleanup — **diferido** (manual usuario)

**Checkpoint G**: PASS → cierre `CLOSED_WITH_ACCEPTED_DEBT`

---

## Cierre documental (post-G)

- [x] `evidence/final-validation.md`
- [x] `evidence/accepted-debt.md`
- [x] `evidence/spec-closure.md`
- Spec 015: **no iniciada**

## Dependencies

- A → B → C then D (prefer C before D)
- E after D
- F docs-only
- G last
