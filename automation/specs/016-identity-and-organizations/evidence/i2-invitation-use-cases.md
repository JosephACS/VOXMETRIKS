# Spec 016 — I2 Invitation use cases

**Fecha:** 2026-07-11  
**Estado:** PASS

## Flujo

Create (token plaintext once, hash stored, `email_delivery_status=not_sent`) → Accept (email match, pending, not expired) → Revoke · Resend.

**Resend:** revoke pending + create replacement (política aprobada). Token anterior deja de aceptar (revoked). Motivo técnico: DuckDB ART no permite UPDATE de `token_hash` UNIQUE.

## Casos cubiertos en tests

duplicate pending · wrong email · expired · used · resend invalida previo · org closed bloquea · audit sin plaintext.
