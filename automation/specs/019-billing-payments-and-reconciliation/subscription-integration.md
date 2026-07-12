# Subscription Integration — Spec 019

## Overview

Billing (019) integrates with Subscriptions (018) via a thin orchestration layer.
Subscriptions NEVER import billing. Billing imports SubscriptionUseCases.

## Orchestration module

`apps/backend/app/packages/billing/application/orchestration.py`

```python
from app.packages.subscriptions.application.use_cases import SubscriptionUseCases

def notify_subscription_past_due(conn, *, subscription_id: int, actor_user_id: int) -> None:
    """Called when invoice becomes past_due. Marks subscription past_due + limits access."""
    SubscriptionUseCases(conn).update_access_state(
        subscription_id,
        actor_user_id=actor_user_id,
        access_state="limited",
        also_set_past_due=True,
        reason="billing_past_due",
    )

def notify_subscription_recovered(conn, *, subscription_id: int, actor_user_id: int) -> None:
    """Called when payment is settled. Restores subscription access."""
    SubscriptionUseCases(conn).update_access_state(
        subscription_id,
        actor_user_id=actor_user_id,
        access_state="full",
        reason="payment_settled",
    )
```

## Trigger points in use cases

| Use Case | Trigger | Action |
|----------|---------|--------|
| MarkInvoicePastDue | invoice.status → past_due | notify_subscription_past_due |
| CreatePaymentAttempt (on failure path) | attempt.status → failed + invoice past_due | notify_subscription_past_due |
| ReconcilePayment | payment.status → reconciled + invoice.status → paid | notify_subscription_recovered |
| RecordManualPayment / ConfirmMockPayment | invoice.status → paid | notify_subscription_recovered |
| AllocatePayment (fully paid) | invoice.status → paid | notify_subscription_recovered |

## Null guard

If `invoice.subscription_id` is NULL, orchestration calls are skipped (non-subscription invoices).

## Import safety

```
billing.application.use_cases → imports billing.application.orchestration
billing.application.orchestration → imports subscriptions.application.use_cases
subscriptions.application.use_cases → NO billing imports
```

No circular dependency.
