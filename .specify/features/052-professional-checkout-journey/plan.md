# Plan — 052 Professional Subscription and Checkout Journey

## Current-state defects

- `personal_subscriptions.start_checkout()` creates a processing subscription and `_cancel_active_non_free()` runs before payment.
- `personal-plans.page.ts` calls checkout and immediately simulates `succeeded`.
- `subscription-select-plan.page.ts` creates an Organization subscription and navigates to overview without invoice/payment orchestration.
- Billing already implements profiles, invoices, token references, attempts, mock provider results, payments, allocations, dunning, refunds and idempotency, but the purchase UI does not compose them.
- Copy and OpenAPI still contain academic/demo terminology.

## Target architecture

### Shared contract, separate domain orchestration

- Add a small frontend `packages/checkout` surface for the common stepper, view model, safe in-memory card mapping and result components.
- Personal orchestration remains under `personal_subscriptions/application/checkout.py` and its tables.
- Organization orchestration remains under `subscriptions/application/checkout.py`, composing existing Subscription and Billing use cases.
- Do not create a generic repository that writes both domains directly. Composition occurs through public application services.

### Transaction boundaries

- Session creation is transactional and idempotent.
- Payment-method attachment is transactional and stores safe metadata only.
- Confirmation rechecks checkout state, ownership, price, invoice and method inside `transactional()`.
- Organization success composes provider result → payment → allocation → invoice paid → subscription active → access refresh in one serialized DuckDB region.
- Personal success composes attempt → invoice paid → selected subscription active → prior paid subscription superseded → entitlements refresh in one transaction.
- Provider simulation performs no network I/O while holding the DuckDB lock.

### Compatibility

- Existing `/api/v1/personal/checkout` and `/payment-attempts/{id}/simulate` delegate to the new Personal orchestrator and are deprecated.
- Existing low-level Billing endpoints remain available to operational roles.
- Existing trial, cancel, refund, dunning and manual-transfer behavior is preserved unless a failing contract requires a narrowly scoped correction.

## Backend work

1. Add idempotent checkout-session and safe payment-method-reference schema for Personal and Organization contexts.
2. Add strict Pydantic request/response models with `extra=forbid` and no raw PAN/CVV fields.
3. Implement Personal checkout lifecycle without pre-payment cancellation.
4. Implement Organization checkout orchestration by composing Billing and Subscription use cases.
5. Make confirm concurrency-safe and replay-safe; preserve append-only attempts/events.
6. Add exact RBAC/tenant dependencies and stable error codes.
7. Replace academic/demo provider descriptions with professional simulation terminology while preserving the explicit `is_mock/is_simulated` truth fields.

## Frontend work

1. Route Personal paid plans to `/account/checkout`; remove automatic success simulation.
2. Route Organization paid plan selection to `/subscriptions/checkout`; trial remains explicit.
3. Implement Review, Billing, Payment, Processing and Result steps with reload/resume support.
4. Keep PAN/CVV only in component memory; map documented test values to safe opaque simulation metadata and clear fields after use.
5. Use server `next_action`, capabilities and status for navigation/CTA visibility.
6. Provide inline validation, accessible alerts/status, disabled double-submit and retry/change-method paths.
7. Refresh Personal/Organization/session context after success.

## Security and data rules

- Never log request bodies containing card inputs.
- Never add PAN/CVV columns, DTOs, fixtures, snapshots or telemetry.
- Do not accept arbitrary `organization_id` from request bodies when context headers already establish tenant.
- Generate idempotency keys once per user intent and persist them in session storage only until checkout completion.
- Errors expose stable codes and no foreign IDs or tenant data.
- Canonical data is read-only during automated acceptance; E2E uses a temporary copy and dedicated personas.

## Verification

- Directed backend: schema, state machines, transaction rollback, concurrency, idempotency and tenant isolation.
- Directed frontend: card memory rules, state reducer, routing, RBAC, retries and context refresh.
- Full backend, `create_app()`, frontend lint/test/build once at closure.
- Isolated Playwright for Personal and Organization success/failure on desktop/mobile.
- Static secret/PAN scan of changed files and fingerprint proof for canonical DuckDB.
