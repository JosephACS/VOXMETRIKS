# I4 — Members & invitations

**Status**: COMPLETE

## Members (`/organizations/:id/members`)

- Listado paginado
- Acciones por permiso: suspend / reactivate / remove / leave / link a roles
- Confirmaciones; 409 mostrado como regla de negocio
- Backend autoridad

## Invitations (`/organizations/:id/invitations`)

- Crear (email, rol, ttl_days)
- Listar / revocar / reenviar
- Modo académico: `delivery_status=not_sent`, token returned-once en banner
- Copiar token; nunca `token_hash`; no localStorage del token

## Accept (`/invitations/accept` + `/invitations/:token/accept`)

- Requiere auth
- Token solo en memoria del flujo
- Errores: email / expired-gone / revoked / used
- Activación opcional post-éxito
