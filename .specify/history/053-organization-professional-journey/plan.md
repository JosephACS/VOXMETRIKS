# Plan — 053 Professional Organization Journey

## Reuse boundaries

- Organizations remains the authority for profile, membership, roles, permissions, invitations and active organization preference.
- Session bootstrap from Spec 050 remains the authority for available spaces and durable return URLs.
- Organization checkout from Spec 052 remains the authority for paid purchase state and entitlement activation.
- Subscriptions/Billing remain the authority for plans, trials, invoices, payment attempts and module-access tier.
- The 053 layer may compose those read models and actions; it must not write their tables directly except through their application services.

## Backend design

1. Add a small `organization_journey` application service and strict presentation models under the Organizations package.
2. Add an idempotent onboarding metadata table keyed by `organization_id` only for explicit completion/optional-step choices and timestamps.
3. Build `GET /api/v1/organizations/{id}/journey` from current organization, membership/capabilities, module-access snapshot, active/pending subscription, checkout and team counts.
4. Add `POST /api/v1/organizations/{id}/journey/complete`; revalidate prerequisites inside `transactional()` and never grant entitlements.
5. Harden organization create/update catalogs and country-derived defaults. Keep server slug generation authoritative and collision-safe.
6. Add invitation-safe role catalog presentation. Do not accept platform roles from client input.
7. Enrich member list output through an additive DTO with safe identity fields while retaining compatibility for existing callers.
8. Keep invitation delivery truth explicit. Gate one-time local links behind configuration and omit them in normal mode.
9. Reuse existing audit facilities and stable error mapping; no swallowed exceptions or cross-tenant identifiers in errors.

## Frontend design

1. Replace the local five-step `OrgOnboardingPageComponent` state with a route-driven/resumable journey based on server `next_action`.
2. Simplify creation to human fields and an optional advanced section. Use shared catalogs for creation and settings.
3. Route paid plan selection into the existing 052 checkout and use checkout result/context refresh to resume 053.
4. Keep trial explicit and no-charge; after activation resume the same journey.
5. Replace hardcoded invitation roles and `user #id` copy with backend role/member presentation.
6. Make team optional for owners, but never skip required plan/payment prerequisites.
7. Complete invitation acceptance by activating the organization and navigating to the first server-authorized destination.
8. Filter Organization administration CTAs/navigation by capabilities; do not hide valid deep links from authorized members.
9. Use one professional status/feedback region per step and responsive controls; no academic/demo terminology.

## State and transaction rules

- Journey reads are side-effect free.
- Creation is idempotent for the same creator intent and cannot reuse a foreign organization.
- Completion is replay-safe and validates organization membership plus owner/admin setup capability.
- Invitation acceptance retains its existing transaction and last-owner/security invariants.
- No network email/payment call is made while a DuckDB transaction lock is held.
- Checkout state and access tier are read, not copied into onboarding metadata.
- Canonical DuckDB is read-only during automated acceptance.

## Compatibility

- Existing organization endpoints and URLs remain valid.
- Existing plan, trial, checkout, settings, member, invitation, role and audit pages are adapted rather than replaced wholesale.
- Old onboarding links redirect into the canonical resumable journey.
- Existing API response fields remain compatible; new presentation fields are additive unless all in-repo callers are migrated in the same package.

## Verification strategy

- Backend directed tests: journey derivation, catalog validation/defaults, idempotency, completion prerequisites, invitation roles, member presentation, RBAC and tenant isolation.
- Frontend directed tests: reducer/view model, creation controls, server next action, checkout/trial handoff, capability filtering, invitation continuation and reload.
- Isolated Playwright: owner paid success, decline/retry, trial and invited viewer at desktop/mobile.
- One closure gate: backend suite once, `create_app()`, frontend lint/test/build, `git diff --check`, OpenAPI checks and canonical DB fingerprint comparison.
