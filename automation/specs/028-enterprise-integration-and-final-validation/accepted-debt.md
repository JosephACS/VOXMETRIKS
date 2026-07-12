# Deferred/Accepted Debt — Spec 028 (post 024/025)

## Accepted debt (unchanged)

| ID | Debt |
|----|------|
| X-01 | Playwright enterprise E2E NOT_VERIFIED |
| X-02 | Docker compose gate NOT_VERIFIED |
| X-03 | DuckDB academic concurrency limits |
| X-04 | No GDPR certification |
| X-05 | MOCK payment/email only |
| X-06 | Runtime ETL partial |

## Removed from deferred (now implemented)

- Executive reporting (024)
- Customer Success (025)
- Support (025)

## Out of scope (honest)

- Royalties / payouts (future specs — **not** numbered 024/025)
- Contractual SLA guarantees
- Spec 029

## Acceptance

System remains **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT** after integrating 024/025.

## Polish-pass notes (no Spec 029)

| Item | Status |
|------|--------|
| Org-scoped billing/subscriptions UI (was hardcoded org id) | Fixed |
| CRM context cleared on org switch | Fixed |
| Expanded opt-in demo seed (CRM→CS path) | Done — still opt-in only |
| Dead FE links (`/billing/invoices/new`, subscription changes) | Removed |
| CRM contacts UI + quotation accept + contract/conversion wiring | Done (completeness pass) |
| Campaign approval decide + CS risks/interventions | Done |
| Bundle size / CSS budget warnings | Accepted historical debt |
| Playwright / Docker | Still **NOT_VERIFIED** |
| Authenticated browser automation in this session | PARTIAL (login gate verified; credentials not entered via automation) |
| Mora/dunning module | Still absent (past_due display only) — accepted debt |
| Auto-provision subscription from CRM conversion | Still manual post-org — by design / accepted debt |
