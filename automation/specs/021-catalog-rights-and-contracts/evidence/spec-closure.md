# Spec Closure — Spec 021 Catalog Rights and Contracts

**Final status:** `CLOSED_WITH_ACCEPTED_DEBT`  
**Date:** 2026-07-12

## Summary
All in-scope backend and frontend deliverables for Spec 021 were implemented, wired, and tested. Catalog rights tracking is organization-scoped, distinct from CRM commercial contracts, with sweep-line percentage validation and conflict detection.

## Tables delivered (11/11)
`app_catalog_asset`, `app_catalog_release`, `app_catalog_asset_artist`, `app_catalog_ownership`, `app_rights_contract`, `app_rights_contract_party`, `app_rights_territory`, `app_rights_authorized_use`, `app_rights_conflict`, `app_rights_approval`, `app_rights_status_history`.

## Use cases delivered (16/16)
RegisterCatalogAsset, LinkWarehouseTrack, CreateRelease, LinkAssetArtist, RegisterOwnership, CreateRightsContract, AddContractParty, SetTerritories, SetAuthorizedUses, SubmitForApproval, ApproveContract, DetectOverlap, OpenConflict, ResolveConflict, ArchiveContract, QueryRightsCoverage, GetContractHistory.

## Permissions delivered (6/6)
`rights.view`, `rights.create`, `rights.update`, `rights.approve`, `rights.conflict`, `rights.archive` — seeded in `organizations/infrastructure/catalogs.py` with requested role matrix.

## Test results
| Suite | Result |
|-------|--------|
| `test_catalog_rights_schema_n1.py` | **32 passed** |
| `test_catalog_rights_use_cases_n2.py` | **36 passed** |
| `test_catalog_rights_api_n3.py` | **19 passed** |
| `test_catalog_rights_security_n5.py` | **11 passed** |
| **Catalog rights total** | **98 passed** |
| `pytest -q` (full backend suite) | **all passed**, exit code 0 |
| `catalog-rights-l4.spec.ts` | service smoke tests present |

## Files delivered
### Backend
`apps/backend/app/packages/catalog_rights/` (domain, application, infrastructure, presentation)

### Frontend
`apps/frontend/src/app/packages/catalog-rights/` (models, services, pages, routes)

### Modified
- `apps/backend/app/main.py` — schema + router wiring
- `apps/backend/tests/conftest.py` — schema bootstrap
- `apps/backend/app/packages/organizations/infrastructure/catalogs.py` — rights permissions
- `apps/frontend/src/app/app.routes.ts`, dashboard nav, i18n en/es

## Accepted debt
See `evidence/accepted-debt.md` — Playwright E2E NOT_VERIFIED, no auto-expiry, warehouse_album_id unvalidated.
