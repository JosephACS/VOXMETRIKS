# I5 — Context invalidation

**Status**: COMPLETE

## Reglas

- Authz se revalida en cada request vía membership + permisos SQL (no cache de permisos en backend).
- Preferencia **no** es fuente de autorización.
- Leave / suspend / remove: si `active_organization_id` apunta a esa org, se limpia la preferencia del usuario afectado.
- Dependencies ya limpiaban preferencia inválida al resolver contexto (`access_revoked` / invalid).
- FE `activate()`: limpia estado scoped **antes** de aplicar nueva org; en error también limpia.

## Platform roles

`ActorContext.is_platform_operator` **ya no** incluye identity `admin`.  
Solo `platform_admin` / `security_admin`. Acceso elevado completo (grants, expiry) **diferido** — deny by default.
