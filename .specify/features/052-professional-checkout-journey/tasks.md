# Tasks — 052 Professional Subscription and Checkout Journey

## Foundation

- [x] T001 Confirm clean branch/base, 0 staged and canonical DB fingerprint; inventory exact callers of legacy checkout/simulate endpoints.
- [x] T002 Add idempotent Personal and Organization checkout-session schemas plus safe token-reference metadata.
- [x] T003 Add strict shared-shaped API models and stable error mapping; prove PAN/CVV fields are rejected.

## Personal journey

- [x] T004 Implement Personal create/get/attach/confirm/cancel state machine in `transactional()`.
- [x] T005 Remove pre-payment `_cancel_active_non_free`; activate/supersede only after success.
- [x] T006 Add immutable attempts, failure/retry/processing, resume and exact event trail.
- [x] T007 Keep legacy endpoints as deprecated adapters and migrate all frontend callers.

## Organization journey

- [x] T008 Implement Organization checkout state machine by composing existing Subscription/Billing use cases.
- [x] T009 Create/issue invoice and pending subscription without granting operational access.
- [x] T010 Confirm atomically: attempt → payment → allocation → invoice paid → subscription active → access refresh.
- [x] T011 Prove concurrency, idempotent replay, rollback at every boundary and cross-tenant isolation.
- [x] T012 Preserve explicit no-charge trial; do not create paid artifacts for trials.

## Frontend

- [x] T013 Add shared checkout models/state reducer/API adapters and resumable routes.
- [x] T014 Implement accessible Review, Billing, Payment, Processing and Result UI for Personal and Organization.
- [x] T015 Implement browser-memory-only test card validation/mapping; clear PAN/CVV after tokenization/navigation.
- [x] T016 Replace Personal automatic success simulation with the canonical checkout journey.
- [x] T017 Replace Organization direct activation with canonical checkout; connect organization onboarding.
- [x] T018 Apply server capabilities to CTA visibility and block double-submit; preserve deep links and return URLs.
- [x] T019 Refresh session, Personal subscription and Organization access after success without logout.
- [x] T020 Replace academic/demo copy in touched payment surfaces with one honest simulated-payment disclosure.

## Verification

- [x] T022 Add directed frontend tests for reducer, validation, memory clearing, failure/retry, navigation and capability parity.
- [x] T021 Add directed backend tests for state transitions, active-plan preservation, rollback, concurrency, replay and tenant/RBAC isolation.
- [x] T023 Run isolated Playwright Personal + Organization success/decline/processing at 1366×768 and 390×844. (10/10 passed against dedicated frontend :4201 and isolated DuckDB/API :8011.)
- [~] T024 Run `create_app()`, frontend lint/test/build locally; defer the full backend suite to the PR CI gate to avoid a duplicate 10–15 minute run.
- [x] T025 Run `git diff --check`, OpenAPI contract checks, changed-file PAN/secret scan and canonical DB fingerprint comparison.
- [x] T026 Deliver exact results and pending risks with 0 staged, 0 commit and 0 push; stop for direct audit.

## Execution rules

- Implement T001–T020 as one bounded Cursor package; do not pause for routine substeps.
- Do not create another Spec.
- Do not rewrite Billing, Subscriptions or Personal Subscriptions wholesale.
- Do not store/transmit raw PAN/CVV or add a real payment provider.
- Do not change royalties, dashboards, AI, ELT or canonical datasets.
- Do not use swallowed exceptions, client-authoritative activation or destructive table replacement.
- Do not stage, commit or push.
