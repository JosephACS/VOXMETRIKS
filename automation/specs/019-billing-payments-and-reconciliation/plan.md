# Plan — Spec 019 Billing, Payments and Reconciliation

**Status:** DESIGN_APPROVED → IMPLEMENTATION_COMPLETE  
**Date:** 2026-07-11

## Architecture decision

- Backend: `apps/backend/app/packages/billing/` (same module pattern as 017/018)
- Frontend: `apps/frontend/src/app/packages/billing/` (Angular standalone components)
- API prefix: `/api/v1/billing`
- Tables: 10 billing-specific tables via `ensure_billing_tables(conn)`
- Provider abstraction: `PaymentProvider` interface + `AcademicMockProvider` (mock) + `ManualTransferRecorder`
- Subscription integration: thin orchestration function in billing calls `SubscriptionUseCases`
- Permission seeding: extends `organizations/infrastructure/catalogs.py`

## Implementation phases

| Phase | Scope |
|-------|-------|
| L0 | Scaffold + schema + feature.json |
| L1 | Tables + schema tests |
| L2 | Use cases + domain tests |
| L3 | API router + API tests |
| L4 | Frontend pages |
| L5 | Security tests + evidence |

## Subscription integration design

```
billing.use_cases.PaymentAttemptFailed / invoice past_due
  → billing.orchestration._notify_subscription_past_due(conn, subscription_id)
      → SubscriptionUseCases(conn).update_access_state(
            subscription_id, access_state="limited", also_set_past_due=True, ...)

billing.use_cases.PaymentSettled / ReconcilePayment
  → billing.orchestration._notify_subscription_recovered(conn, subscription_id)
      → SubscriptionUseCases(conn).update_access_state(
            subscription_id, access_state="full", ...)
```

Import order avoids circular: `billing.orchestration` imports from `subscriptions.application.use_cases`; subscriptions never imports billing.

## Key design choices

1. Academic Mock Provider: labeled `[MOCK]` in display names and API responses
2. Ledger: trigger guard raises Python error on attempted UPDATE/DELETE (enforced at use-case layer)
3. Credit notes: create a negative invoice-like document; apply against future invoices or trigger refund
4. Partial payments: `app_payment_allocation` links payment → invoice with amount; invoice tracks `amount_paid`
