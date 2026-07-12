# Checklist — Spec 019 Billing, Payments and Reconciliation

## Schema
- [x] 10 billing tables created (app_billing_profile, app_invoice, app_invoice_item, app_payment_method_reference, app_payment_attempt, app_payment, app_payment_allocation, app_refund, app_credit_note, app_payment_provider_event, app_billing_ledger_entry)
- [x] app_payment_attempt.idempotency_key UNIQUE constraint
- [x] app_payment_provider_event.provider_event_id UNIQUE constraint
- [x] NO PAN/CVV columns in any table
- [x] Invoice status CHECK: draft, issued, partially_paid, paid, past_due, void, partially_credited, credited
- [x] Payment attempt status CHECK: created, processing, succeeded, failed, canceled
- [x] Payment status CHECK: recorded, settled, reconciled, partially_refunded, refunded, reversed

## Use cases
- [x] CreateBillingProfile
- [x] IssueInvoice
- [x] VoidInvoice
- [x] CreateCreditNote
- [x] CreatePaymentAttempt (idempotent)
- [x] RecordManualPayment
- [x] ConfirmMockPayment
- [x] AllocatePayment
- [x] ReconcilePayment
- [x] MarkInvoicePastDue
- [x] RetryPayment
- [x] RefundPayment
- [x] ReversePayment
- [x] ProcessProviderEvent (idempotent)
- [x] CreatePaymentMethodReference (no PAN/CVV)

## Subscription integration
- [x] PaymentAttemptFailed → UpdateAccessState(limited, also_set_past_due=True)
- [x] PaymentSettled → UpdateAccessState(full) + recover active
- [x] No circular imports (billing imports subscriptions; not vice versa)

## Security
- [x] billing.view permission for read-only
- [x] billing.manage permission for mutations
- [x] Cross-tenant access blocked
- [x] No raw card data accepted or stored
- [x] Mock provider clearly labeled [MOCK]

## Frontend
- [x] Billing profile page
- [x] Invoice list + detail
- [x] Payment attempts list
- [x] Manual transfer form
- [x] Reconciliation view
- [x] Refunds view
- [x] Credit notes view
- [x] Ledger view
- [x] Past-due banner
- [x] Mock payments labeled

## Tests
- [x] L1 schema tests
- [x] L2 use case tests
- [x] L3 API tests
- [x] L5 security tests
- [x] Ledger immutability test
- [x] No PAN/CVV columns test
- [x] Subscription access updated test
- [x] Idempotency key test
- [x] Duplicate webhook test
