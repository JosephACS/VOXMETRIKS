# Feature and Entitlement Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## feature (catálogo platform)

`feature_id` · `code` (único) · `display_name` · `description?` · `value_type` (`boolean`|`limit`|`enum`) · `unit?` · `is_active`

Ejemplos de **códigos** (no compromisos de producto): `members.max`, `artists.max`, `analytics.advanced`, `exports.enabled`, `history.days`.

---

## plan_feature

`plan_feature_id` · `plan_id` · `feature_id` · `limit_value?` · `enabled` · timestamps

Define qué incluye el plan.

---

## subscription_entitlement (efectivo org-scoped)

`entitlement_id` · `subscription_id` · `organization_id` · `feature_code` · `limit_value?` · `enabled` · `source` (`plan`|`addon`|`override`) · `access_effect` hint · timestamps

### Reglas
| ID | Regla |
|----|-------|
| BR-ENT-01 | Features usadas ⊆ entitlements activos (BR-SUB-01) |
| BR-ENT-02 | Materializar al activate/trial/change; no confiar solo en plan join runtime sin snapshot |
| BR-ENT-03 | Override platform auditado |
| BR-ENT-04 | Deny by default si feature no entitlement |

### Relación con access
Entitlement **habilita** capacidad; `access_state` de la subscription (o por feature) puede degradar a limited/blocked sin borrar entitlement row (histórico).
