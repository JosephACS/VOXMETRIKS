# 046 — Security

## Autenticación

- Todos los endpoints requieren sesión (`Authorization: Bearer`).
- Artist Space **no** exige `X-Organization-Id`.

## Autorización

1. **Membership-gated**: el usuario debe tener membership `active` en el `artist_profile_id` del path.
2. **Permission codes** derivados del rol (no RBAC org).
3. **Isolation**: user A nunca ve memberships/spaces/requests de user B.
4. **Engineer identity**: sin membership → sin acceso Artist Space (403/empty mine).
5. **Platform Admin**: solo endpoints `/platform/artist-requests/*`; no bypass de membership en `/artist-space/*` salvo esos endpoints de revisión.
6. **Invite accept**: token one-time; expired/revoked rechazados; email debe coincidir con usuario autenticado (normalize).
7. **Last owner**: no revocar ni degradar el único owner activo.
8. **Promote to owner**: prohibido vía PATCH role e invite.

## Datos sensibles

- Nunca devolver `token_hash` ni plaintext en listados.
- Plaintext token solo en respuesta de create invitation (`returned_once`).
