# Accepted Debt — Spec 021

Status at closure: **CLOSED_WITH_ACCEPTED_DEBT**

## 1. Playwright E2E browser verification — NOT_VERIFIED
No live-browser Playwright run against catalog-rights pages. Confidence from:
- Backend API suite (`test_catalog_rights_api_n3.py`, 19 tests)
- Use-case suite (`test_catalog_rights_use_cases_n2.py`, 36 tests)
- Frontend service unit tests (`catalog-rights-l4.spec.ts`)

**Risk:** low-medium — visual/interaction regressions uncaught until manual testing.

## 2. No automatic contract expiry
`valid_to` passing does not auto-transition `status` to `expired`. Status changes are manual or via approval/archive workflows only.

**Risk:** low — documented business rule; future spec may add scheduled job.

## 3. warehouse_album_id unvalidated
No `dim_album` physical table in this warehouse. `warehouse_album_id` on `app_catalog_release` is stored as opaque optional reference with no existence check.

**Risk:** low — optional metadata only.

## 4. No SQL compound UNIQUE constraints
Natural-key uniqueness (one pending approval per contract) enforced in use cases, not SQL UNIQUE — consistent with artists/billing DuckDB posture.

**Risk:** low — all production access via use-case layer.

## 5. Coverage and approvals as detail-page sections
Dedicated top-level routes for coverage (`/coverage`) and approvals (`/approvals`) were not created; functionality lives on asset-detail and contract-detail pages respectively.

**Risk:** low — all API endpoints covered; nav points to parent list pages.

## 6. app_rights_contract ≠ app_commercial_contract — enforced by design
No join path exists. CRM commercial contracts remain in Spec 017 domain only.

**Risk:** none — intentional separation.
