# Tasks — 053 Professional Organization Journey

## Foundation

- [ ] T001 Confirm branch/base, 0 staged and canonical DB fingerprint; inventory exact Organization/Subscription/Checkout callers.
- [ ] T002 Add idempotent onboarding metadata schema and shared validated organization catalogs.
- [ ] T003 Add strict journey, creation, invitation-role and member-presentation schemas with stable errors.

## Backend composition

- [ ] T004 Implement side-effect-free Organization Journey read model from existing domain authorities.
- [ ] T005 Implement replay-safe completion with server prerequisites and no entitlement writes.
- [ ] T006 Harden organization create/update defaults, catalogs, collision behavior and client intent idempotency.
- [ ] T007 Add invitation-safe assignable role catalog and validate assignments server-side.
- [ ] T008 Add safe member identity/role presentation without cross-tenant leakage.
- [ ] T009 Enforce invitation delivery mode and remove normal-mode token exposure.
- [ ] T010 Add audit events and prove rollback/concurrency/tenant isolation.

## Frontend journey

- [ ] T011 Replace local onboarding steps with server-driven resumable journey state.
- [ ] T012 Simplify organization creation and share human catalogs with settings.
- [ ] T013 Integrate plan/trial/052 checkout handoff and resume after reload/result.
- [ ] T014 Implement capability-aware Team step with backend role options and human member presentation.
- [ ] T015 Complete invite acceptance/activation destination using Spec 050 return URL/session bootstrap.
- [ ] T016 Add professional waiting/retry/forbidden/conflict feedback for non-owner and incomplete states.
- [ ] T017 Filter touched Organization administration CTAs/navigation by exact capabilities and access tier.
- [ ] T018 Preserve post-onboarding editability in Settings/Members/Invitations/Roles.
- [ ] T019 Remove technical IDs, raw statuses, token copy and academic/demo copy from touched surfaces.

## Verification

- [ ] T020 Add directed backend tests for journey derivation, validation, idempotency, RBAC and isolation.
- [ ] T021 Add directed frontend tests for server next actions, creation, handoffs, capabilities and reload.
- [ ] T022 Run isolated Playwright owner paid success, decline/retry, trial and invited viewer on desktop/mobile.
- [ ] T023 Run `create_app()`, full backend once, frontend lint/test/build and OpenAPI contract checks.
- [ ] T024 Run `git diff --check`, changed-file secret/token scan and canonical DB fingerprint comparison.
- [ ] T025 Deliver exact results, changed files and true residual risks with 0 staged, 0 commit and 0 push.

## Execution rules

- Implement T001–T019 as one bounded Cursor package; do not pause for routine substeps.
- Do not create another Spec.
- Do not rewrite Organizations, RBAC, Subscriptions, Billing, Checkout or session bootstrap wholesale.
- Do not touch CRM, Customer Success, Compliance, Campaigns, Royalties, analytics, AI, ELT or canonical datasets.
- Do not expose raw PAN/CVV, invitation tokens, internal IDs or foreign-tenant state.
- Do not use client-authoritative access, swallowed exceptions or destructive table replacement.
- Do not stage, commit or push.
