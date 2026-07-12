# Lifecycle State Machines — Spec 019

## Invoice states
```
draft
  │ IssueInvoice
  ▼
issued ────────────────────────────── VoidInvoice → void
  │                                           │
  │ AllocatePayment (partial)                 │
  ▼                                           │
partially_paid ─── AllocatePayment (full) ──► paid
  │                                           │
  │ MarkInvoicePastDue                        │ CreateCreditNote (full)
  ▼                                           ▼
past_due                              partially_credited → credited
```

## Payment Attempt states
```
created
  │ provider.initiate_attempt
  ▼
processing
  │                │
  │ succeeded      │ failed
  ▼                ▼
succeeded        failed ──► RetryPayment → new attempt
  │
  │ creates Payment(status=recorded)
  ▼
(Payment entity created)
```

## Payment states
```
recorded
  │ SettlePayment (provider confirms)
  ▼
settled
  │ ReconcilePayment (accounting match)
  ▼
reconciled
  │                │
  │ RefundPayment  │ ReversePayment
  ▼                ▼
partially_refunded  reversed
  │ (full refund)
  ▼
refunded
```

## Credit Note states
```
draft → issued → applied
                   │
                 voided (if not yet applied)
```

## Subscription integration triggers
```
PaymentAttemptFailed (invoice.status → past_due)
  └─► SubscriptionUseCases.update_access_state(
        access_state="limited", also_set_past_due=True)

PaymentSettled / ReconcilePayment
  └─► SubscriptionUseCases.update_access_state(
        access_state="full")
      SubscriptionUseCases.renew (if period renewal)
```
