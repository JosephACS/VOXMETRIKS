# L0 — Schema Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** PASS

## Tables Created by `ensure_billing_tables`

| Table | Key Constraints |
|---|---|
| `app_billing_profile` | UNIQUE(organization_id) |
| `app_invoice` | CHECK(status IN …), UNIQUE(organization_id, invoice_number) |
| `app_invoice_item` | FK-like organization_id, invoice_id |
| `app_payment_method_reference` | No PAN/CVV columns |
| `app_payment_attempt` | UNIQUE(idempotency_key) |
| `app_payment` | CHECK(status IN …) |
| `app_payment_allocation` | |
| `app_refund` | CHECK(status IN …) |
| `app_credit_note` | CHECK(status IN …) |
| `app_payment_provider_event` | UNIQUE(provider_event_id) |
| `app_billing_ledger_entry` | Append-only (no UPDATE/DELETE) |

## Test Results

File: `tests/test_billing_schema_l1.py` — **25/25 PASS**

Covered:
- All 11 tables exist after `ensure_billing_tables`
- idempotency_key UNIQUE constraint fires on duplicate
- provider_event_id UNIQUE constraint fires on duplicate
- billing_profile UNIQUE(organization_id)
- No PAN/CVV columns in payment_method_reference
- Ledger update raises ConstraintException
- Ledger delete raises ConstraintException
- Invoice CHECK state transitions
- Currency consistency CHECK
- Billing permissions seeded in `app_permission`
- Role permission mappings for owner, billing_manager, finance

## Command

```bash
python -m pytest tests/test_billing_schema_l1.py -v
```
