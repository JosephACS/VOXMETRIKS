# L3 — Security Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** PASS

## Security Controls Verified

| Control | Test |
|---|---|
| Cross-tenant isolation | org_b cannot read org_a billing profile → 403 |
| Cross-tenant isolation | org_b cannot see org_a invoices → 403 |
| Cross-tenant isolation | org_b cannot see org_a ledger → 403 |
| No PAN/CVV columns | Schema test confirms absence |
| Mock provider labeled | `is_mock=True` on all AcademicMockProvider attempts |
| Ledger immutability | UPDATE raises, DELETE raises |
| Subscription past_due | Access state updated on failed attempt |
| Subscription recovered | Access state updated on payment settled |

## Test Results

File: `tests/test_billing_security_l5.py` — **7/7 PASS**

Covered:
- cross_tenant_profile_isolation
- cross_tenant_invoice_isolation
- cross_tenant_ledger_isolation
- no_pan_cvv_columns
- mock_provider_flagged
- ledger_immutable_on_update
- subscription_access_updated_on_past_due

## RBAC Table

Uses `app_role_permission` (not `app_business_role_permission`) for org-level checks.

## Accepted Debt

- Playwright / E2E browser tests not implemented (no browser test framework configured in this workspace)
- Platform roles `platform_finance` and `platform_admin` break-glass billing access deferred

## Command

```bash
python -m pytest tests/test_billing_security_l5.py -v
```
