# I5 — Invitation security

**Status**: COMPLETE

## Controles

- Entropía: `secrets.token_urlsafe(32)`
- Persistencia: solo SHA-256 hex
- Verify: `hmac.compare_digest`
- Resend: revoke+create (token anterior inválido)
- Accept: single-use; re-check in TX; no double membership activa
- Anti-oracle: email mismatch → `InvitationNotFound` / HTTP 404 (igual que token desconocido)
- Returned-once solo en create/resend response
- FE: ruta `/invitations/:token/accept` eliminada (Referer/history)

## Pruebas

`test_accept_email_mismatch_anti_oracle`, `test_resend_invalidates_old_token_and_duplicate_accept`, API i3 invitations flow.
