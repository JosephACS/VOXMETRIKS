# Tasks: Identity and First Access Orchestration

## Phase 1 — Baseline and tests

- [X] T001 Record initial branch/HEAD/status and confirm the canonical DB is untouched.
- [X] T002 Add independent temporary-DB tests reproducing the identity schema readiness defect.
- [X] T003 Add backend contract tests for bootstrap/context, isolation and revoked memberships.
- [X] T004 Add frontend tests for `returnUrl`, post-auth resolution and multi-space fallback.

## Phase 2 — Backend authority

- [X] T005 Fix schema readiness per connection/database without weakening startup performance.
- [X] T006 Implement session bootstrap by composing existing identity/org/artist/platform/household services.
- [X] T007 Implement atomic context activation and stable capability reason codes.
- [X] T008 Centralize shared password validation for register/reset/change; keep PIN separate.
- [X] T009 Make Free provisioning explicit/idempotent and remove silent onboarding failure.

## Phase 3 — Frontend orchestration

- [X] T010 Preserve and validate local `returnUrl` in auth guards/interceptor.
- [X] T011 Implement one post-auth orchestrator for login/register verification/Google/session restore.
- [X] T012 Make `SpaceContextService`, menus and guards consume the bootstrap manifest.
- [X] T013 Connect household profile resolution only for Personal destinations.
- [X] T014 Add first-run intent actions: Listen, Artist, Organization; no permission grants.
- [X] T015 Restore visible “I am an artist” and organization entry paths.

## Phase 4 — Form and presentation closure

- [X] T016 Remove favorite genre and development internals from registration; add confirmation and shared policy messages.
- [X] T017 Make verification/recovery durable and preserve success/error state.
- [X] T018 Replace technical organization inputs/codes in the touched onboarding path with generated/catalog-backed controls.
- [X] T019 Remove role-only/username-demo routing authority after consumers migrate.
- [X] T020 Fix the two mechanical frontend lint errors already present in the baseline.

## Phase 5 — Acceptance

- [X] T021 Run directed and full backend tests with isolated basetemp; zero order dependence.
- [X] T022 Run frontend lint, full tests and build; zero errors.
- [X] T023 Run Playwright scenarios from SC-004 in desktop/mobile and verify logout cross-account isolation.
- [X] T024 Run `git diff --check`, inspect changed-file scope and confirm canonical DB hash/mtime unchanged.
- [X] T025 Report exact results and stop with 0 staged/commit/push for direct audit.
