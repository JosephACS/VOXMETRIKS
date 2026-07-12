# Audit and Security — Spec 021

## Tenant isolation
- Every use case validates `organization_id` on read/write.
- Cross-tenant resource IDs return `NotFoundError` → HTTP 404 (no information leak).

## Permission enforcement
- `require_org_rights_permission(code)` dependency checks membership + role matrix.
- Missing permission → HTTP 403.

## Audit trail
- Mutations call `_audit()` → `AuditRepository.append` with `source="catalog_rights.use_case"`.
- Contract status changes also append to `app_rights_status_history`.

## Data integrity
- No mutation of `dim_track` or CRM `app_commercial_contract`.
- Overlap detection runs after party add and territory set.
- Archived contracts excluded from overlap calculation.

## Headers
- `X-Organization-Id` required (mirrors artists/billing pattern).
- `Authorization: Bearer` required for all endpoints.
