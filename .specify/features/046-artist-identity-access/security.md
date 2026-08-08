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
6. **Invite accept**: token one-time; expired/revoked rechazados; email debe coincidir con usuario autenticado (normalize). Email mismatch → `PermissionDenied` **sin** cambiar status ni crear membership.
7. **Last owner**: no revocar ni degradar el único owner activo.
8. **Promote to owner**: prohibido vía PATCH role e invite.
9. **Invite ops** (`list` / `revoke` / `resend` / `create`): requieren `artist_space.invite`. Team membership revoke/role change: `artist_space.team.manage`.

## Invitation token handling

- **Accept token solo en JSON body**: `POST /artist-invitations/accept` con `{ "token": "..." }`.
- **Nunca** poner el token en el path URL (`/{token}/accept` eliminado).
- Nunca loguear el plaintext token.
- FE accept page: formulario paste + submit; no lee `:token` de la ruta.

## Invitation lifecycle endpoints

| Método | Path | Permiso |
|--------|------|---------|
| GET | `/artist-space/{id}/invitations?status=` | `artist_space.invite` |
| POST | `/artist-space/{id}/invitations` | `artist_space.invite` |
| POST | `/artist-space/{id}/invitations/{iid}/revoke` | `artist_space.invite` |
| POST | `/artist-space/{id}/invitations/{iid}/resend` | `artist_space.invite` |
| POST | `/artist-invitations/accept` | session user + email bind |

- Solo `pending` se puede revocar → `revoked` (no quita membership; accepted → ValidationError).
- Resend genera **nuevo** token/hash, extiende `expires_at`; el token anterior falla de inmediato. No duplica pending por email.
- Accepted invitation no se “revoca como invite”; usar team revoke para membership.

## Datos sensibles

- Nunca devolver `token_hash` ni plaintext en listados.
- Plaintext token solo en respuesta de **create** y **resend** invitation (`returned_once`, `email_delivery_status=not_sent`).
