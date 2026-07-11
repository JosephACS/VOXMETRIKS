# I5 — Compatibility

**Status**: COMPLETE

## Confirmado

- Login/logout/`/me` fixtures (pytest auth_headers)
- Personal routes sin org obligatoria (`test_user_without_org_keeps_personal_api`, i3 personal routes)
- Roles técnicos user/admin/engineer intactos; **no** bypass org
- `app_user` warehouse: **5** (sin alteración I5)
- ELT/warehouse facts intactos (`validate_warehouse.py` OK)
- No backfill automático de orgs/memberships en I5
- Tests usan DuckDB temporal / pytest DB — no smoke de creación contra warehouse principal

## Nota warehouse principal

Lectura I5: `app_organization=10`, memberships/invites/audit con filas de sesiones previas (I3 residual / uso manual). I5 **no** ejecutó creación permanente en warehouse. Identity permanece en 5 usuarios.
