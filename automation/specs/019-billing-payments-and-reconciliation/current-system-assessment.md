# Current System Assessment — Spec 019

**Date:** 2026-07-11  
**Assessor:** Implementation agent

## What exists (post-018)

| Component | State |
|-----------|-------|
| DuckDB warehouse | 10 subscription tables + all org/crm/contract tables |
| `app_subscription` | Fully functional with past_due status |
| `SubscriptionUseCases.update_access_state` | Stub callable ready for billing hooks |
| `app_organization` | Has `default_currency`, `timezone` columns |
| Platform RBAC | platform_admin, platform_engineer, etc. |
| Org catalogs | billing_manager, finance roles seeded (no billing.* perms yet) |
| Backend test suite | ~304 passing (post-018) |
| Frontend | Angular; billing package not yet present |

## What is missing (019 scope)

- No billing tables (profile, invoice, payment, ledger, etc.)
- No `/api/v1/billing` routes
- No frontend billing pages
- No billing.view / billing.manage permissions seeded
- No PaymentProvider abstraction

## Integration points

- `app_subscription.id` is the FK for billing → subscription integration
- `app_organization.default_currency` is used as billing profile currency default
- `app_audit_log` available for billing audit writes
- `using_write_conn()` context manager available for write operations
