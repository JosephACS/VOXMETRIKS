# L4 — Frontend Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** IMPLEMENTED (unit tests written)

## Pages Created

| Page | File | Route |
|---|---|---|
| Billing Profile | `billing-profile.page.ts` | /billing/profile |
| Invoice List | `invoices-list.page.ts` | /billing/invoices |
| Payment Attempts | `payment-attempts.page.ts` | /billing/payment-attempts |
| Manual Transfer | `manual-transfer.page.ts` | /billing/manual-transfer |
| Reconciliation | `reconciliation.page.ts` | /billing/reconciliation |
| Refunds | `refunds.page.ts` | /billing/refunds |
| Credit Notes | `credit-notes.page.ts` | /billing/credit-notes |
| Ledger | `ledger.page.ts` | /billing/ledger |

## Services

- `BillingApiService` — HTTP client for all billing endpoints
- Mock payments clearly labeled with `[MOCK]` badge in UI

## Past-Due Banner

- Shown on invoices list when any invoice is in `past_due` state
- Calls `markPastDue()` action

## Unit Tests

File: `apps/frontend/src/app/packages/billing/services/billing-l4.spec.ts`

Covered:
- BillingApiService.getProfile() calls correct endpoint
- BillingApiService.listInvoices() calls correct endpoint
- BillingApiService.createPaymentAttempt() passes idempotency_key
- BillingApiService.recordManualPayment() calls /payments/manual
- BillingApiService.getLedger() calls /ledger

## Accepted Debt

- No Playwright / E2E browser tests (accepted, no browser test framework)
- Pages use mock data stubs; real HTTP integration requires backend running
