# L5 — Full Test Run Evidence (Spec 019)

**Date:** 2026-07-11  
**Status:** ALL PASS

## Billing Test Suite

```
tests/test_billing_schema_l1.py   25 tests  PASS
tests/test_billing_use_cases_l2.py 18 tests PASS
tests/test_billing_api_l3.py      11 tests  PASS
tests/test_billing_security_l5.py  7 tests  PASS
─────────────────────────────────────────────
Total billing                      61 tests  PASS
```

## Full Suite (all specs)

```
451 tests collected
451 passed (revalidated parent sprint 2026-07-11)
0 failed
0 errors
```

Previously failing tests fixed:
- `test_crm_schema_j1.py::test_auditor_permissions_restricted` — updated allowed set to include `plan.view` (added by Spec 018)
- `test_organizations_schema_i1.py::test_seed_roles_permissions_exact` — removed `billing.view` from "no future permissions" ban list (billing permissions implemented in Spec 019)

## Commands

```bash
# Billing only
python -m pytest tests/test_billing_schema_l1.py tests/test_billing_use_cases_l2.py tests/test_billing_api_l3.py tests/test_billing_security_l5.py -v

# Full suite
python -m pytest tests/ -q
```
