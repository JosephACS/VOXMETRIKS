# J3 — API and platform RBAC

**Status**: PASS

## Prefix
`/api/v1/crm`

## AuthZ
- Bearer required
- `require_crm_permission(code)` via `app_user_platform_role` matrix
- Deny by default
- Identity `admin`/`engineer`/`user` do **not** imply CRM
- Org roles do **not** imply CRM

## Endpoint groups
prospects · contacts · opportunities · activities · quotations/versions/items · approvals · conversions · audit · permissions  
contracts under `/api/v1/crm/contracts`

## Error mapping
401 / 403 / 404 / 409 / 410 / 422

## Tests
`test_crm_api_j3.py` — PASS
