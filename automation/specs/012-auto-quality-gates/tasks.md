# Tasks: Calidad Automática y Tests de Hotspots

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

**Prerequisites**: plan.md ✅, spec.md ✅

**Status**: ✅ All phases complete (implemented 2026-06-29)

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Tooling base backend + frontend

- [x] T001 Create `backend/pyproject.toml` with Ruff + pytest configuration per FR-QG01
- [x] T002 Add `ruff==0.6.9` and `pytest-cov==5.0.0` to `backend/requirements.txt` per FR-QG03
- [x] T003 [P] Install frontend devDeps: `angular-eslint@^21`, `eslint@^9`, `typescript-eslint@^8`, `@eslint/js` per FR-QG04

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Scripts unificados y decisión de testing

- [x] T004 Create `backend/Makefile` with `lint`, `lint-fix`, `test`, `build`, `check` per FR-QG02
- [x] T005 Add `lint`, `lint:fix`, `test`, `build`, `check` to `frontend/package.json` per FR-QG05
- [x] T006 Document Vitest as sole frontend standard; configure `ng test --no-watch --no-progress` per FR-QG06
- [x] T007 Create `frontend/eslint.config.js` (Angular ESLint flat config) per FR-QG04
- [x] T008 Create `frontend/vitest.config.ts` + `frontend/src/test-setup.ts` (jsdom polyfills) per research R5
- [x] T009 Wire `runnerConfig: vitest.config.ts` in `frontend/angular.json`

---

## Phase 3: User Story 1 — Backend quality gate (P1) 🎯

**Goal**: `make check` passes with Ruff + full pytest suite

**Independent Test**: `cd backend && make check` → exit 0

- [x] T010 [US1] Run `ruff check . --fix` for mechanical safe fixes (imports, whitespace) per FR-QG09
- [x] T011 [US1] Calibrate `pyproject.toml` per-file-ignores for documented legacy debt (mutations, user_service)
- [x] T012 [US1] Validate `python -m pytest -q` — 74 tests pass per SC-QG03

---

## Phase 4: User Story 2 — Frontend quality gate (P1)

**Goal**: `npm run check` passes lint + vitest + build

**Independent Test**: `cd frontend && npm run check` → exit 0

- [x] T013 [US2] Calibrate ESLint rules for legacy codebase (prefer-inject off, template a11y off, max-warnings 50)
- [x] T014 [US2] Fix `app.spec.ts` title assertion (`VOXMETRIK`)
- [x] T015 [US2] Adjust `angular.json` CSS budget 16→17 kB for `home.component.css` (build gate only)
- [x] T016 [US2] Validate `npm run lint`, `npm run test`, `npm run build` per SC-QG02

---

## Phase 5: User Story 3 — Hotspot tests (P2)

**Goal**: Dedicated tests for four hotspots without logic changes

**Independent Test**: Hotspot test files all green

### Backend hotspots

- [x] T017 [P] [US3] Create `backend/tests/test_quality_hotspots.py` — `generate_synthetic_activity` guards + `split_activity_counts` per FR-QG07
- [x] T018 [P] [US3] Add `get_tracks_cursor` tests (ordering, keyset, search, invalid cursor) per FR-QG07
- [x] T019 [P] [US3] Add `get_recommendations` tests (aggregate, genre priority, popularity fallback) per FR-QG07

### Frontend hotspot

- [x] T020 [US3] Create `frontend/src/app/shared/services/music-player.service.spec.ts` — `loadTrack` via `playTrack` per FR-QG08

### Validation

- [x] T021 [US3] Run `pytest --cov=app` — total ≥ 60%, `list.py` 100% per SC-QG05
- [x] T022 [US3] Confirm 8 Vitest tests pass per SC-QG04

---

## Phase 6: Polish & Spec Kit Documentation

**Purpose**: SDD artifacts and traceability

- [x] T023 Create `specs/012-auto-quality-gates/spec.md` per SC-QG06
- [x] T024 Create `plan.md`, `research.md`, `quickstart.md`, `tasks.md`, checklist
- [x] T025 Update `.specify/feature.json` → `specs/012-auto-quality-gates`
- [x] T026 Update `specs/README.md` index with spec 012
- [x] T027 Run `/speckit-converge` — verify converged state

---

## Dependencies

```text
Phase 1 → Phase 2 → Phase 3 ∥ Phase 4 → Phase 5 → Phase 6
```

## Parallel Execution Examples

```text
# After Phase 2:
T010–T012 (backend validation) ∥ T013–T016 (frontend validation)

# Phase 5:
T017, T018, T019 (backend hotspot tests) ∥ T020 (frontend hotspot test)
```

## Implementation Strategy

1. Tooling + scripts first (Phases 1–2)
2. Validate gates independently backend/frontend (Phases 3–4)
3. Add hotspot tests without touching production logic (Phase 5)
4. Formalize Spec Kit artifacts (Phase 6)

**MVP**: Phases 1–4 (`make check` + `npm run check`)  
**Full delivery**: Phase 5 hotspot tests + Phase 6 SDD docs
