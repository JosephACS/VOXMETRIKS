# Addon Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## addon (catálogo)

`addon_id` · `code` · `display_name` · `feature_code` · `limit_delta?` · `status` (`active`|`retired`) · timestamps

## addon_price (opcional separado o embebido)

`addon_price_id` · `addon_id` · `currency` · `billing_period` · `amount` · `status`

Misma honestidad: configurable, no FX, snapshot en change.

## Reglas
| ID | Regla |
|----|-------|
| BR-ADD-01 | Addon se aplica vía `subscription_change` |
| BR-ADD-02 | Recalcula entitlements (sum limits / enable flags) |
| BR-ADD-03 | No crear invoice en 018 |
| BR-ADD-04 | Addon retired no se añade a nuevas; existentes siguen hasta remove |

## Ejemplos ilustrativos (no compromisos)
extra artists seats · extra members · export pack — **códigos demo**.
