# Spec 016 — I2 Transactions and rollback

**Fecha:** 2026-07-11  
**Estado:** PASS

## Helper

`application/transactions.py` — `BEGIN` / `COMMIT` / `ROLLBACK` sobre la misma conexión DuckDB.

## Atómicos

- CreateOrganization (org+member+role+activate+pref+audit)
- AcceptInvitation (membership+role+accepted+audit)
- Ownership/role changes with last-owner guard
- Preference set/clear

## Rollback test

`test_create_rollback_on_role_failure` — forced failure en `assign_member_role` → 0 orgs, 0 memberships.
