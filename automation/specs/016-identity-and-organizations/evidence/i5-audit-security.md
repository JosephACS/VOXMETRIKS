# I5 — Audit security

**Status**: COMPLETE

## Cobertura sensible (success)

create/update/status org; membership suspend/reactivate/left/remove; invitation create/accept/revoke/resend; role assign/revoke; preference change/clear.

## Reglas verificadas

- Append-only repo (no update/delete API).
- `_FORBIDDEN_KEYS` sanitiza tokens/hashes/passwords/Authorization.
- Create invitation audita sin plaintext token.
- Suite I5: blob audit sin `invite_token` / `token_hash`.
- Org admins no tienen endpoint de edición de auditoría.

## Deuda aceptada

Auditoría de denegaciones (result=denied) no implementada de forma exhaustiva en cada 403/404 (coste/ruido académico).
