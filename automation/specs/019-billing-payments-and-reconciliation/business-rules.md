# Business Rules — Spec 019

## BR-001: One billing profile per organization
One `app_billing_profile` per `organization_id`. Attempting to create a second raises `BillingProfileExistsError`.

## BR-002: Currency immutability
Invoice currency must equal `billing_profile.default_currency`. After first invoice issued, profile currency cannot be changed.

## BR-003: Invoice item immutability
Once invoice status = `issued`, items cannot be added, updated, or deleted. Corrections require a credit note.

## BR-004: Backend totals
`invoice.total` and `invoice.subtotal` are always computed as `SUM(items.amount)` at use-case layer. Clients cannot set totals directly.

## BR-005: Idempotent payment attempt
Same `idempotency_key` → return existing `PaymentAttempt`, HTTP 200. No duplicate processing.

## BR-006: Idempotent provider event
Same `provider_event_id` per `provider_code` → return existing event, HTTP 200. No duplicate processing.

## BR-007: Subscription past_due on payment failure
When invoice transitions to `past_due`, billing orchestration calls `SubscriptionUseCases.update_access_state(access_state="limited", also_set_past_due=True)`.

## BR-008: Subscription recovery on payment
When payment is settled and invoice is paid, billing orchestration calls `SubscriptionUseCases.update_access_state(access_state="full")`.

## BR-009: Ledger append-only
`app_billing_ledger_entry` rows cannot be UPDATEd or DELETEd. Any attempt raises `LedgerImmutableError`. Corrections via new adjustment entries.

## BR-010: No raw payment credentials
`app_payment_method_reference` stores only provider tokens and masked display labels. No PAN, CVV, expiry date, or full card numbers.

## BR-011: Refund ≤ payment amount
`refund.amount` cannot exceed the total amount of the associated payment minus already-refunded amounts.

## BR-012: Credit note ≤ invoice total
`credit_note.amount` cannot exceed `invoice.total`.

## BR-013: Mock provider labeling
`AcademicMockProvider` always uses `provider_code = "academic_mock"` and display name starting with `[MOCK]`. API responses include `is_mock: true`.

## BR-014: Partial payment tracking
`invoice.amount_paid` updated on each `AllocatePayment`. Status transitions: issued → partially_paid → paid based on `amount_paid` vs `total`.

## BR-015: Single currency per invoice
All items on an invoice must share the invoice's currency. Mixed-currency invoices are rejected.
