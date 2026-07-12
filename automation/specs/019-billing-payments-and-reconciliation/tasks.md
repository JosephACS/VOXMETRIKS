# Tasks — Spec 019 Billing, Payments and Reconciliation

**Status:** DONE  
**Last updated:** 2026-07-11

## L0 — Scaffold
- [x] Create spec documentation directory
- [x] Write all design documents (spec, plan, models, etc.)
- [x] Update feature.json → 019

## L1 — Schema
- [x] `billing/infrastructure/schema.py` with `ensure_billing_tables`
- [x] Wire in `apps/backend/app/main.py` lifespan (before mark_schema_ready)
- [x] Wire in `apps/backend/tests/conftest.py`
- [x] `test_billing_schema_l1.py` — all 10 tables + constraints

## L2 — Use cases
- [x] `billing/domain/entities.py` — dataclasses for all billing entities
- [x] `billing/domain/errors.py` — billing-specific errors
- [x] `billing/application/use_cases.py` — all 15 use cases
- [x] `billing/application/orchestration.py` — subscription integration
- [x] `test_billing_use_cases_l2.py` — idempotency, states, partial payments, allocations

## L3 — API
- [x] `billing/presentation/schemas.py` — Pydantic request/response models
- [x] `billing/presentation/error_mapping.py`
- [x] `billing/presentation/dependencies.py`
- [x] `billing/presentation/router.py` — all endpoints
- [x] Wire billing router in `main.py`
- [x] `test_billing_api_l3.py` — all endpoints

## L4 — Frontend
- [x] `frontend/src/app/packages/billing/` pages
- [x] Routes and nav integration
- [x] Unit tests

## L5 — Security + Evidence
- [x] `test_billing_security_l5.py` — cross-tenant, no PAN/CVV, permission checks
- [x] Evidence files
- [x] TRACEABILITY-MASTER.md updated
