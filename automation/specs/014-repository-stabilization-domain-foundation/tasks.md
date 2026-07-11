# Tasks: Estabilización del Repositorio y Fundación Package-by-Domain

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)  
**Prerequisites**: Autorización explícita del usuario para ejecutar (draft actual)  
**Status**: Pending approval — correcciones post-revisión externa

## Format: `[ID] [P?] [Story] Description`

---

## Phase A: Baseline y respaldo

**Purpose**: Rama limpia + evidencia de salud previa; no tocar trabajo ajeno

- [ ] T001 Create git branch `014-repository-stabilization-domain-foundation` from current HEAD
- [ ] T002 Run `git status`. If there are changes unrelated to 014, **stop** and show them to the user. Do **not** stash, reset, or commit unrelated work without explicit authorization.
- [ ] T003 Run available backend pytest (summary only); abort 014 if suite already broken unrelated to 014
- [ ] T004 [P] Run available frontend `npm run test` / `build` / `lint` (summary only)
- [ ] T005 Record baseline summary (commit message of 014-only baseline commit if tree is clean for 014, or short note under this spec folder). Verify G8 (no secrets/generated files staged).

**Checkpoint A**: Baseline green or failures pre-documented; working tree authorized → continue. Rollback: delete branch / reset to pre-A commit.

---

## Phase B: Constitución y gobierno (US1)

**Purpose**: Enmienda puntual — no reescritura total

- [ ] T006 [US1] Patch `.specify/memory/constitution.md`: monorepo `apps/` + `analytics/` + `automation/` + `infrastructure/`
- [ ] T007 [US1] Patch constitution: specs live in `automation/specs/` (not inside `.specify`)
- [ ] T008 [US1] Patch constitution: package-by-domain técnico vs dominios empresariales futuros; ban empty modules
- [ ] T009 [US1] Patch constitution: real audio state — YouTube + Audius fallback + demo (not WAV-only). Audius retained: active in `apps/backend/app/packages/streaming/services/audio/audius_provider.py` wired by `resolver.py`
- [ ] T010 [US1] Patch constitution: OpenSpec/Spec Kit required before relevant structural changes; honest naming AI/Enterprise/RC
- [ ] T011 [US1] Patch constitution: principle **negocio → objetivos → procesos → actores → casos de uso → reglas → datos → backend → frontend → reportes → IA**
- [ ] T012 [US1] Set `.specify/feature.json` → `automation/specs/014-repository-stabilization-domain-foundation`
- [ ] T013 Commit: `docs(constitution): align monorepo and package-by-domain rules for spec 014` (rollback = revert this commit)

**Checkpoint B**: Constitution diff reviewed

---

## Phase C: Frontend consolidation (US2)

**Purpose**: Absorb `features/` into `packages/`; keep route paths

- [ ] T014 [US2] Map `features/dashboard` → target under `packages/`; update `app.routes.ts` imports only
- [ ] T015 [US2] Map `features/analytics` → `packages/analytics`; dedupe with existing analytics component
- [ ] T016 [US2] Map `features/tracks` (insights) → `packages/` without colliding CRUD `/tracks`
- [ ] T017 [US2] Introduce `packages/identity|catalog|engagement` folders only when moving real code (no empty dirs)
- [ ] T018 [US2] Optionally rename `layouts/` → `shell/` with re-exports if low-risk; else defer
- [ ] T019 [US2] Remove obsolete `features/` files after zero imports
- [ ] T020 [US2] Run `npm run lint`, `npm run test`, `npm run build`; verify G2 (app loads + login) if runtime available
- [ ] T021 [US2] Run Playwright if available; else document skip
- [ ] T022 Commit: `refactor(frontend): consolidate features into packages (spec 014)` (rollback = revert)

**Checkpoint C**: Routes unchanged; FE gates pass or documented

**Do not**: modify player code; delete MusicPlayerService; integrate playback-core

---

## Phase D: Backend consolidation (US3)

**Purpose**: Packages + `/api/v1` facade + documented security on sensitive routes

- [ ] T023 [US3] Add compatibility shims: `packages/users` re-exports → `packages/identity` (or rename with shim path)
- [ ] T024 [US3] Split or alias `packages/streaming` into `catalog` + `engagement` with temporary re-exports preserving import paths
- [ ] T025 [US3] Keep `packages/analytics` and `packages/ai`; ensure `main.py` still mounts working routers
- [ ] T026 [US3] Define **canonical `/api/v1` facade** that preserves FE-consumed contracts; choose per-endpoint implementation via consumers, tests, and security — **do not** declare Packages V1 as the entire canonical API. Keep enterprise V1 + V2 as adapters while consumers exist.
- [ ] T027 [US3] Apply coherent auth to sensitive routes (documented security exception to “no functional change”); verify G4 (401/403 without permission) without breaking authenticated FE flows (G3)
- [ ] T028 [US3] Update imports across backend; keep temporary `from app.packages.users…` shims
- [ ] T029 [US3] Run pytest; verify G1 (backend starts)
- [ ] T030 Commit: `refactor(backend): package-by-domain foundation with /api/v1 facade (spec 014)` (rollback = revert)

**Checkpoint D**: FE contracts OK; auth gates recorded

---

## Phase E: ELT canonical declaration (US4)

- [ ] T031 [US4] Declare `analytics/elt` as canonical pipeline in Makefile/docs used by ops
- [ ] T032 [US4] **Do not delete** `apps/backend/app/etl`. Create an adapter invoking `analytics/elt` **only if parity is demonstrable** (same critical outcomes). Otherwise document gap and leave boot path on `app/etl`. No DuckDB schema changes.
- [ ] T033 [US4] Preserve `RUN_ETL_ON_BOOT` behavior
- [ ] T034 [US4] Capture before/after row counts for critical tables: `dim_track`, `dim_artista`, `dim_album`, `fact_streaming`, `app_user`, `app_session`, `app_playlist`, `app_favorite`. Justify deltas or stop/rollback (G5, G6). Run warehouse scripts if available; else document skip.
- [ ] T035 Commit only if docs/adapter landed: `docs(elt): declare analytics/elt canonical; keep app/etl (spec 014)` (rollback = revert)

**Checkpoint E**: Boot usable; schema unchanged; row counts OK or justified

---

## Phase F: Playback — documentation only (US5)

- [ ] T036 [US5] Document future direction only: intended SoT = `playback-core`; `MusicPlayerService` remains the active player in 014 (constitution pointer or short note in this spec folder / plan progress — **docs only**)
- [ ] T037 [US5] **No player code changes.** Do not integrate `playback-core`. Do not refactor `MusicPlayerService`. Confirm `git diff` has zero playback/player source changes for this phase.
- [ ] T038 [US5] Confirm `MusicPlayerService` remains in place (no deletion)
- [ ] T039 [US5] Run existing playback-related vitest specs; smoke G7 (basic playback) if runtime available — report only
- [ ] T040 [US5] Commit **only if documentation files changed**: `docs(playback): record future SoT direction for post-014 (spec 014)`. Never a playback code refactor commit.

**Checkpoint F**: Docs + test results only; G7 holds; no player code diff

---

## Phase G: Cleanup

- [ ] T041 Remove legacy imports/shims only after grep shows zero consumers
- [ ] T042 Archive unused route modules if any; do not delete with uncertainty
- [ ] T043 Update `README.md`, `docs/QUICKSTART.md`, Docker, Makefile, `.github/workflows/ci.yml` if needed
- [ ] T044 Update TRACEABILITY evidence paths for renamed packages (or explicit debt)
- [ ] T045 Final validation: G1–G9 as applicable (pytest + FE check + e2e + login + playback smoke + no secrets)
- [ ] T046 Commit: `chore: post-014 cleanup and docs alignment` (rollback = revert)

**Checkpoint G**: Spec 014 complete or remaining gaps listed in checklist

---

## Dependencies

- A → B → C then D (prefer C before D)
- E after D
- F docs-only; may run after B; must not touch player during C
- G last

## Parallel opportunities

- T004 ∥ T003  
- Within C: sequential by route collision risk  
- D shims before auth tightening (T027)
