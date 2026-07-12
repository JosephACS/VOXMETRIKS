# Test Strategy — Spec 021

## Backend (pytest)
| Suite | File | Count | Focus |
|-------|------|-------|-------|
| N1 Schema | `test_catalog_rights_schema_n1.py` | 32 | Tables, CHECK constraints, permissions matrix, dim_track untouched, rights ≠ commercial_contract |
| N2 Use cases | `test_catalog_rights_use_cases_n2.py` | 36 | %, overlap, territory, conflict, approval, coverage, warehouse link |
| N3 API | `test_catalog_rights_api_n3.py` | 19 | HTTP contracts, pagination, conflict responses |
| N5 Security | `test_catalog_rights_security_n5.py` | 11 | Cross-tenant, permission gaps |

**Total catalog_rights: 98 tests**

## Frontend
| Suite | File | Focus |
|-------|------|-------|
| L4 Unit | `catalog-rights-l4.spec.ts` | HTTP method/URL/header smoke for all API service methods |

## E2E
Playwright browser E2E: **NOT_VERIFIED** (accepted debt, consistent with 016–020).

## Regression
Full backend `pytest -q` must pass with zero regressions in artists, billing, CRM, etc.
