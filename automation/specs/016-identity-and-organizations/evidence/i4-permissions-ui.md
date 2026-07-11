# I4 — Permissions UI

**Status**: COMPLETE

## Roles page

`/organizations/:id/roles` — catálogo sistema + permisos (solo lectura de catálogo).

Assign/revoke vía PUT member roles (permiso `role.assign`).

## Guards (UX only)

- `organizationPathContextGuard` — sync activate por `:id`
- `organizationPermissionGuard(code)` → `/access-denied`
- Estados: `/organizations/none|suspended|closed`, `/access-denied`

## Separación

Roles técnicos `user|admin|engineer` no se mezclan con roles organizacionales en UI de org.
