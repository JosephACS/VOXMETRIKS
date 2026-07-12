# Test Strategy — Spec 019

## Test files

| File | Suite | Scope |
|------|-------|-------|
| `test_billing_schema_l1.py` | L1 | Table existence, constraints, no PAN/CVV |
| `test_billing_use_cases_l2.py` | L2 | Domain use cases, idempotency, states |
| `test_billing_api_l3.py` | L3 | HTTP endpoints (TestClient) |
| `test_billing_security_l5.py` | L5 | Cross-tenant, permissions, no PAN/CVV, mock label |

## L1 — Schema tests
- All 11 billing tables created
- idempotency_key UNIQUE on app_payment_attempt
- provider_event_id UNIQUE on app_payment_provider_event
- NO PAN/CVV columns (introspect columns, assert not in list)
- Invoice status CHECK: invalid → error
- Payment attempt status CHECK: invalid → error
- Billing.view / billing.manage permissions seeded in catalogs

## L2 — Use case tests
- CreateBillingProfile creates profile
- Duplicate profile raises BillingProfileExistsError
- IssueInvoice transitions draft → issued
- IssueInvoice with no items raises ValidationError
- VoidInvoice transitions issued → void
- CreatePaymentAttempt idempotent (same key returns same record)
- RecordManualPayment creates payment + ledger entries
- AllocatePayment partial → partially_paid; full → paid
- MarkInvoicePastDue transitions issued → past_due
- Subscription access updated on past_due (mock subscription check)
- Subscription access recovered on payment
- CreateCreditNote + ApplyCreditNote
- Ledger UPDATE raises LedgerImmutableError
- Ledger DELETE raises LedgerImmutableError

## L3 — API tests
- GET /billing/profile → 200 or 404
- POST /billing/profile → 201
- POST /billing/invoices → 201 (draft)
- POST /billing/invoices/{id}/issue → 200
- POST /billing/payment-attempts → 201 (idempotency test)
- POST /billing/manual-transfer → 201
- GET /billing/ledger → 200

## L5 — Security tests
- Cross-tenant: org_A user cannot access org_B billing profile → 403
- Missing billing.view → 403
- No PAN/CVV columns in DB introspection
- Mock provider labeled [MOCK]
- Provider event duplicate → 200 idempotent

## E2E / Playwright
**NOT_VERIFIED** — Playwright environment not available in this project context. Accepted debt.
