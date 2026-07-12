# Subscription Change Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## subscription_change

### Campos
`change_id` · `subscription_id` · `organization_id` · `change_type` · `from_plan_id?` · `to_plan_id?` · `from_price_id?` · `to_price_id?` · `addon_id?` · `status` · `effective_at` · `scheduled_for?` · `reason?` · `requested_by` · `applied_at?` · timestamps

### change_type
`upgrade` · `downgrade` · `period_change` · `addon_add` · `addon_remove` · `cancel_schedule` · `reactivate` · `entitlement_override` · `access_update`

### status
`pending` · `scheduled` · `applied` · `canceled` · `rejected`

### Reglas
| ID | Regla |
|----|-------|
| BR-CHG-01 | Todo cambio de plan/addon/cancel → fila change (BR-SUB-04) |
| BR-CHG-02 | Downgrade destructivo puede requerir confirmación / aplazar a period end (HUM004) |
| BR-CHG-03 | Scheduled: no aplicar antes de `scheduled_for` |
| BR-CHG-04 | Al apply: rematerializar entitlements + evento EntitlementsChanged |
| BR-CHG-05 | Emitir señal billable hacia Billing **sin** crear invoice aquí |

### Proration
Política **configurable/diferida** — no afirmar prorrateo monetario sin Billing.
