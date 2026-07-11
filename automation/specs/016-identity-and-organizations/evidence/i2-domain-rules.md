# Spec 016 — I2 Domain rules

**Fecha:** 2026-07-11  
**Estado:** PASS

## Módulos

| Archivo | Contenido |
|---------|-----------|
| `domain/rules.py` | slug/email normalize; org/member/invite transitions; last-owner predicate; platform role codes |
| `domain/errors.py` | errores tipados (sin HTTPException) |
| `domain/events.py` | eventos conceptuales (sin bus) |
| `domain/invitation_token.py` | secrets + SHA-256 hash; returned_once; delivery=not_sent |

## Transiciones org

provisioning→active · active→suspended_by_platform · suspended→active · active/suspended→closed  
**closed→active** rechazado (reopen diferido).

## Idempotencia create

Sin columna/tabla `idempotency_key` en I1 → **no inventada**.  
Protección: slug único + retry del mismo `created_by` reutiliza org existente (`slug_deterministic`).  
**Deuda:** idempotencia fuerte por request key.
