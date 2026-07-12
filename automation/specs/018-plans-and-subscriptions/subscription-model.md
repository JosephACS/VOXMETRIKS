# Subscription Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Scope:** organization · **Deps:** Organizations 016

---

## subscription

### Campos
`subscription_id` · `organization_id` · `plan_id` · `plan_price_id` · `status` · `billing_currency` · `billing_period` · `price_amount_snapshot` · `current_period_start` · `current_period_end` · `trial_ends_at?` · `cancel_at_period_end` · `canceled_at?` · `expired_at?` · `activation_source` (`trial`|`manual`|`billing_event`|`crm_handoff`) · `access_state` · `created_by` · timestamps

### Estados
`trialing` · `active` · `past_due` · `canceled` · `expired`

### Reglas
| ID | Regla |
|----|-------|
| BR-SUB-018-01 | Org debe estar `active` (no closed; suspended bloquea writes sensibles) |
| BR-SUB-018-02 | Una billing_currency por subscription |
| BR-SUB-018-03 | v1: como máximo una subscription en {trialing, active, past_due} por org (HUM003) |
| BR-SUB-018-04 | `active` ≠ “pagada”; paid solo vía evento billing futuro |
| BR-SUB-018-05 | past_due solo por orquestación ante evento financiero fallido |
| BR-SUB-018-06 | No crear subscription sin entitlements materializados |
| BR-SUB-018-07 | No hard delete |

### Actores
create/change/cancel: `owner`, `billing_manager` (org) · platform break-glass auditado.
