# Tasks: 051 Professional Artist Journey

## Phase 1 — Baseline and executable contracts

- [X] T001 Record branch, HEAD, status, canonical DB hash/mtime and the unrelated Listener paths that MUST be preserved.
- [X] T002 Add temporary-DB backend contract tests for discovery actions, request evidence, workspace provisioning, migration idempotency and rollback.
- [X] T003 Add backend RBAC/isolation tests for all artist roles and Platform review.
- [X] T004 Add frontend tests for canonical navigation, human role/status labels, explicit artist selection and zero false-success paths.

## Phase 2 — Identity and tenant foundation

- [X] T005 Extend artist schemas/profile/request models idempotently per data-model.md.
- [X] T006 Implement transactional hidden artist-workspace provisioning by composing the Organizations domain.
- [X] T007 Migrate legacy `organization_id=0` profiles idempotently; never mutate warehouse tables.
- [X] T008 Enrich artist discovery with management state and one server-authoritative allowed action.
- [X] T009 Extend artist permissions for catalog/draft/submit and align backend/frontend capability manifests.
- [X] T010 Harden request review, evidence validation, stable errors and audit trails.

## Phase 3 — Canonical Artist Space

- [X] T011 Replace the claim/create/access UI with a choice-driven responsive wizard and friendly request states.
- [X] T012 Implement editable profile fields with country/genre controls, URL validation, external identifiers and role-aware legal data.
- [X] T013 Consolidate tracks/releases into the Artist Space Music surface with filters and role-aware CTA.
- [X] T014 Complete team/access UI: invite role select, resend/revoke, approve/reject, role change, confirmations and feedback.
- [X] T015 Filter Artist Space navigation and actions using the server capability manifest.

## Phase 4 — Publishing integration

- [X] T016 Add artist-scoped publishing dependencies/routes that resolve the hidden tenant and delegate to existing use cases.
- [X] T017 Refactor the release wizard into reusable organization/artist contexts without copying the state machine.
- [X] T018 Require an explicit artist in Organization Catalog and the active artist in Artist Space; delete all first-profile fallback behavior.
- [X] T019 Support multiple tracks, persisted drafts, media, contributors and rights with strict failure propagation.
- [X] T020 Enforce collaborator draft vs owner/admin submit permissions in backend and frontend.
- [X] T021 Add Platform Ops independent-submission review and preserve organization review for labels/distributors.
- [X] T022 Prove request-changes, resubmit, approve and idempotent publish with append-only history and self-review prevention.

## Phase 5 — Navigation and compatibility

- [X] T023 Make Artist Space the individual portal and Organization Catalog the multi-artist portal; remove duplicate primary navigation entries.
- [X] T024 Keep legacy artist/profile/release URLs working through redirects or shared components; do not delete functioning domain code.
- [X] T025 Refresh session/space context after approvals, invitations, team changes and publication without logout.
- [X] T026 Ensure hidden artist workspaces never appear as ordinary organizations or expose irrelevant CRM/billing/CS menus.

## Phase 6 — Acceptance and audit

- [X] T027 Run directed backend/frontend tests while implementing; fix only scope-related failures.
- [X] T028 Run full backend, `create_app()`, frontend lint/test/build once at closure.
- [X] T029 Run Playwright artist journeys for all required personas at desktop/mobile on an isolated DB.
- [X] T030 Verify OpenAPI/models, relative links, `git diff --check`, scope and canonical DB integrity.
- [X] T031 Deliver exact files/results/pending risks with 0 staged, 0 commit and 0 push; stop for direct audit.

## Execution rules

- Implement T001–T026 as one bounded Cursor package; do not pause for routine substeps.
- Do not create another Spec.
- Do not redesign payments, royalties, analytics, AI or general dashboards.
- Do not use `except Exception: pass`, wholesale file replacement or swallowed RxJS errors.
- Do not stage, commit or push.
