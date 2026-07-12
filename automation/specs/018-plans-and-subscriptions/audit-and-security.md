# Audit and Security — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Principios
Deny by default · backend authority · org isolation · no PAN/CVV · no fake paid · reuse `app_audit_log`.

## Auditoría obligatoria
plan publish/retire · price changes · subscription create · change apply · cancel · reactivate · access_state changes · entitlement overrides · usage adjustments.

Sanitizar: tokens, passwords, Authorization headers.

## Controles
| Amenaza | Control |
|---------|---------|
| Cross-org subscription read | organization_id + membership |
| IDOR | path org vs resource org match |
| Catalog publish by org user | platform permission only |
| Mark paid forged | no public endpoint |
| Immediate cancel bypass | policy + 403 |
| Second active sub | unique constraint / 409 |
| admin identity bypass | BR-SEC-SUB-04 |

## Tests diseño
Ver `test-strategy.md`.
