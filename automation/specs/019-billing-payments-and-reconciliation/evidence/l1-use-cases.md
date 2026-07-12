# L1 — Use Cases Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** PASS

## Use Cases Implemented

| Use Case | Class | File |
|---|---|---|
| CreateBillingProfile | BillingProfileUseCases.create | application/use_cases.py |
| UpdateBillingProfile | BillingProfileUseCases.update | application/use_cases.py |
| IssueInvoice | InvoiceUseCases.create / issue | application/use_cases.py |
| VoidInvoice | InvoiceUseCases.void | application/use_cases.py |
| CreateCreditNote | CreditNoteUseCases.create | application/use_cases.py |
| ApplyCreditNote | CreditNoteUseCases.apply | application/use_cases.py |
| AddPaymentMethod | PaymentMethodUseCases.add | application/use_cases.py |
| RemovePaymentMethod | PaymentMethodUseCases.remove | application/use_cases.py |
| CreatePaymentAttempt | PaymentAttemptUseCases.create | application/use_cases.py |
| ConfirmMockPayment | PaymentAttemptUseCases.confirm_mock | application/use_cases.py |
| RecordManualPayment | PaymentUseCases.record_manual | application/use_cases.py |
| AllocatePayment | PaymentUseCases.allocate | application/use_cases.py |
| ReconcilePayment | PaymentUseCases.reconcile | application/use_cases.py |
| RefundPayment | RefundUseCases.create | application/use_cases.py |
| ReversePayment | PaymentUseCases.reverse | application/use_cases.py |
| MarkInvoicePastDue | InvoiceUseCases.mark_past_due | application/use_cases.py |
| ProcessProviderEvent | ProviderEventUseCases.process | application/use_cases.py |
| GetLedger | LedgerUseCases.list | application/use_cases.py |

## Subscription Integration

- `notify_subscription_past_due(org_id, conn)` → calls `SubscriptionUseCases.update_access_state` with `past_due`
- `notify_subscription_recovered(org_id, conn)` → calls `SubscriptionUseCases.update_access_state` with `active`
- Orchestration function in `application/orchestration.py` — no circular imports

## Test Results

File: `tests/test_billing_use_cases_l2.py` — **18/18 PASS**

Covered:
- create_billing_profile returns entity with correct fields
- duplicate profile raises BillingProfileExistsError
- issue_invoice creates invoice in issued state
- void_invoice raises when already void
- ledger_immutable_on_update raises
- ledger_immutable_on_delete raises
- create_payment_attempt idempotency
- duplicate idempotency_key returns same attempt
- wrong_currency_invoice raises CurrencyMismatchError
- payment_allocation_exceeds_payment raises
- refund_exceeds_payment raises
- credit_note_apply reduces invoice balance
- mark_invoice_past_due transitions state
- provider_event_dedup idempotency
- subscription_past_due_called_on_failed_attempt (via orchestration mock)
- subscription_recovered_called_on_settled_payment (via orchestration mock)
- reconcile_payment transitions to reconciled
- reverse_payment transitions to reversed

## Command

```bash
python -m pytest tests/test_billing_use_cases_l2.py -v
```
