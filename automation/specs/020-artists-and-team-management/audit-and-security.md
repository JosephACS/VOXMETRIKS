# Audit & Security — Spec 020

## Audit trail
Every state-mutating use case (`create`, `activate`, `deactivate`,
`archive`, `link_warehouse_artist`, `transfer_organization`,
`link` [organization], `assign_manager`, `end_assignment`, `add_member`,
`remove_member`, `set_identifier`) calls the shared `_audit()` helper,
writing an `app_audit_log` row via
`app.packages.organizations.infrastructure.repositories.audit_repository.AuditRepository`
— the same mechanism billing uses. Each entry records `action`,
`target_type='artist_profile'` (or sub-entity), `target_id`,
`actor_user_id`, `organization_id`, `previous_values`/`new_values` (where
applicable), and `request_id`.

In addition, every artist-profile status change appends an immutable row to
`app_artist_status_history` (belt-and-suspenders trail specific to this
domain, independent of the generic audit log).

## RBAC
- Organization-scoped via `X-Organization-Id` header + `require_user_id`.
- Permission check via `app_role_permission` join (identical shape to
  billing's `require_org_billing_permission`), gated per-endpoint by the
  granular `artist.*` codes (see `role-and-permission-model.md`).
- Cross-tenant access is blocked at the use-case layer
  (`_get_or_raise_for_org` raises `NotFoundError` rather than leaking
  existence of another org's artist) — verified in
  `test_artists_security_m5.py::test_cross_tenant_get_blocked` and related.

## Data protection
- No PII beyond `display_name`/`legal_name` (already covered by existing
  data-handling policy for org member names).
- No destructive DuckDB operations — all schema changes are additive
  (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).
- `dim_artista` (analytics warehouse) is read-only from this package's
  perspective; verified untouched by `test_artist_profile_schema_m1.py`
  (`dim_artista` untouched) and `test_artists_security_m5.py`
  (`test_dim_artista_never_mutated`).

## Known limitation (documented, not a security gap)
DuckDB's spurious `ConstraintException` on UPDATE (see `data-model.md`) was
observed during implementation and worked around via a `DELETE + INSERT`
pattern for `app_artist_profile` field mutations. This is a correctness/
availability concern (would otherwise surface as intermittent 503s), not a
security vulnerability, and is fully covered by regression tests.
