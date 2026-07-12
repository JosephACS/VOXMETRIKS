# K0 — Setup & Feature Pointer

**Status**: DONE  
**Date**: 2026-07-11

## Actions taken

- `feature.json` already pointed to `018` (no change needed).
- Created package scaffold: `apps/backend/app/packages/subscriptions/` with all `__init__.py` files for `domain`, `application`, `infrastructure`, `presentation`, `routes`.
- `ensure_subscription_tables` wired in `apps/backend/app/main.py` lifespan (before `mark_schema_ready`).
- `ensure_subscription_tables` also called in `apps/backend/tests/conftest.py` `_init_test_database`.

## Critical rules confirmed

- No invoice/payment tables — verified by schema assertions in K1 tests.
- `schema_ready` reset properly in isolated test fixtures following CRM pattern.
