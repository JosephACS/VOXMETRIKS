# L2 — API Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** PASS

## API Endpoints

All under prefix `/api/v1/billing/`

| Method | Path | Permission |
|---|---|---|
| GET | /profile | billing.view |
| PUT | /profile | billing.manage |
| GET | /invoices | invoice.view |
| POST | /invoices | invoice.create |
| GET | /invoices/{id} | invoice.view |
| GET | /invoices/{id}/items | invoice.view |
| POST | /invoices/{id}/issue | invoice.create |
| POST | /invoices/{id}/void | invoice.void |
| POST | /invoices/{id}/mark-past-due | billing.manage |
| POST | /payment-methods | billing.manage |
| DELETE | /payment-methods/{id} | billing.manage |
| POST | /payment-attempts | payment.manage |
| POST | /payment-attempts/{id}/confirm-mock | payment.manage |
| POST | /payments/manual | payment.manage |
| POST | /payments/{id}/allocate | payment.manage |
| POST | /payments/{id}/reconcile | payment.manage |
| POST | /payments/{id}/reverse | payment.manage |
| GET | /payments | payment.view |
| POST | /refunds | refund.manage |
| GET | /refunds | payment.view |
| POST | /credit-notes | credit_note.manage |
| POST | /credit-notes/{id}/apply | credit_note.manage |
| GET | /credit-notes | billing.view |
| GET | /ledger | billing.view |
| POST | /provider-events | billing.manage |

## Test Results

File: `tests/test_billing_api_l3.py` — **11/11 PASS**

Covered:
- GET /profile returns 200 with profile data
- PUT /profile updates and returns 200
- GET /invoices returns list
- GET /invoices/{id} returns invoice detail
- GET /invoices/{id}/items returns items
- POST /payment-attempts idempotency (same key → same response)
- Payment attempt is_mock flag set for AcademicMockProvider
- POST /payments/manual records payment and returns 201
- GET /ledger returns append-only entries
- Missing org header returns 400
- Missing auth returns 401

## Command

```bash
python -m pytest tests/test_billing_api_l3.py -v
```
