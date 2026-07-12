# Tasks — Spec 021 Catalog Rights and Contracts

## Phase 0 — Setup
- [X] T0.1 Create spec folder scaffold and feature.json pointer
- [X] T0.2 evidence/m0-setup.md

## Phase N1 — Schema
- [X] T1.1 `ensure_catalog_rights_tables` — 11 tables + indexes
- [X] T1.2 Wire schema in `main.py` and `conftest.py`
- [X] T1.3 `test_catalog_rights_schema_n1.py` (32 tests)

## Phase N2 — Use Cases
- [X] T2.1 Domain entities and errors
- [X] T2.2 CatalogAsset / CatalogRelease / CatalogAssetArtist / CatalogOwnership use cases
- [X] T2.3 RightsContract / Party / Territory / AuthorizedUse use cases
- [X] T2.4 Sweep-line overlap detection + conflict open/resolve
- [X] T2.5 Approval workflow (submit / approve / reject)
- [X] T2.6 QueryRightsCoverage + GetContractHistory
- [X] T2.7 `test_catalog_rights_use_cases_n2.py` (36 tests)

## Phase N3 — API
- [X] T3.1 Presentation schemas, dependencies (`X-Organization-Id`), error_mapping
- [X] T3.2 Router under `/catalog-rights` prefix
- [X] T3.3 `test_catalog_rights_api_n3.py` (19 tests)

## Phase N4 — Permissions
- [X] T4.1 Seed `rights.*` in `organizations/infrastructure/catalogs.py`
- [X] T4.2 Role matrix: owner all; administrator most; artist_manager view/create/update; finance view; viewer view

## Phase N5 — Security
- [X] T5.1 Cross-tenant NotFoundError masking
- [X] T5.2 Permission enforcement at API layer
- [X] T5.3 `test_catalog_rights_security_n5.py` (11 tests)

## Phase N6 — Frontend
- [X] T6.1 Models + API service
- [X] T6.2 Pages: assets, releases, contracts, conflicts; coverage on asset detail; approvals on contract detail
- [X] T6.3 Routes, dashboard nav, i18n (en/es)
- [X] T6.4 `catalog-rights-l4.spec.ts` unit smoke tests

## Closure
- [X] T7.1 Full docs set (plan, data-model, business-rules, api-contracts, etc.)
- [X] T7.2 evidence/spec-closure.md — CLOSED_WITH_ACCEPTED_DEBT
- [X] T7.3 TRACEABILITY-MASTER.md updated for 020 and 021
