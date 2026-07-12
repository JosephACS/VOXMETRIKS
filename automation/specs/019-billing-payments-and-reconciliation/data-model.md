# Data Model — Spec 019

## Tables (10 billing-specific)

```
app_billing_profile (id, organization_id UNIQUE, default_currency, legal_name,
    tax_id, billing_address, email, status, created_at, updated_at)

app_invoice (id, organization_id, billing_profile_id, subscription_id,
    invoice_number UNIQUE, currency, status, subtotal, total,
    amount_paid, amount_due, period_start, period_end, due_date,
    issued_at, paid_at, voided_at, notes, created_at, updated_at)

app_invoice_item (id, invoice_id, description, quantity, unit_price,
    amount, period_start, period_end, created_at)

app_payment_method_reference (id, organization_id, provider_code, display_label,
    token_ref, method_type, is_default, status, created_at, updated_at)
    -- NO PAN/CVV columns

app_payment_attempt (id, organization_id, invoice_id, payment_method_ref_id,
    provider_code, idempotency_key UNIQUE, amount, currency, status,
    provider_attempt_id, failure_reason, created_at, updated_at)

app_payment (id, organization_id, payment_attempt_id, provider_code,
    amount, currency, status, provider_payment_id, settled_at,
    reconciled_at, created_at, updated_at)

app_payment_allocation (id, payment_id, invoice_id, organization_id,
    amount, created_at)

app_refund (id, organization_id, payment_id, amount, currency, reason,
    status, processed_at, created_at, updated_at)

app_credit_note (id, organization_id, invoice_id, credit_note_number UNIQUE,
    amount, currency, reason, status, issued_at, applied_at,
    created_at, updated_at)

app_payment_provider_event (id, provider_code, provider_event_id UNIQUE,
    event_type, payload, processed, processed_at, created_at)

app_billing_ledger_entry (id, organization_id, entry_type, reference_type,
    reference_id, amount, currency, description, created_at)
    -- APPEND-ONLY
```

## Indexes
- `idx_invoice_org` on `app_invoice(organization_id)`
- `idx_invoice_billing_profile` on `app_invoice(billing_profile_id)`
- `idx_payment_attempt_invoice` on `app_payment_attempt(invoice_id)`
- `idx_payment_org` on `app_payment(organization_id)`
- `idx_payment_allocation_invoice` on `app_payment_allocation(invoice_id)`
- `idx_refund_payment` on `app_refund(payment_id)`
- `idx_credit_note_invoice` on `app_credit_note(invoice_id)`
- `idx_ledger_org` on `app_billing_ledger_entry(organization_id)`
- `idx_provider_event_provider` on `app_payment_provider_event(provider_code)`
