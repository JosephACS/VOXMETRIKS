# Migration and Compatibility — Spec 019

## Backward compatibility

All 019 changes are additive:
- 10 new tables (all `CREATE TABLE IF NOT EXISTS`)
- New org-scoped permissions added to `organizations/infrastructure/catalogs.py`
- New router added to `main.py` (existing routes unchanged)
- No 018 subscription tables modified

## Schema migration

`ensure_billing_tables(conn)` is idempotent and called before `mark_schema_ready()`.
Called in both `main.py` lifespan and `tests/conftest.py` `_init_test_database`.

## Permission migration

New billing permissions added to `PERMISSIONS` catalog in `organizations/infrastructure/catalogs.py`.
`ensure_organization_role_catalogs` inserts missing permissions idempotently.
Existing 018 subscriptions permissions remain unchanged.

## Data migration

No data migration required — all new tables start empty.
No existing columns modified.

## Frontend migration

New billing routes added to `app.routes.ts` without modifying existing routes.
New billing nav items added to org layout nav.

## Test compatibility

Existing tests (K1–K5 subscriptions, J1–J5 CRM) continue to pass.
New L1–L5 billing tests added as separate files.
`conftest.py` updated to call `ensure_billing_tables` after `ensure_subscription_tables`.
