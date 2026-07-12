# Data Model (conceptual) — Spec 018

**Status**: IMPLEMENTATION_COMPLETE  
**Naming final `app_*` confirmed.** Tables created via `ensure_subscription_tables` in DuckDB.

---

## Tablas implementadas (FINAL)

| Conceptual | Física (FINAL) | Owner | Scope | Plan statuses |
|------------|----------------|-------|-------|---------------|
| plan | `app_plan` | subscriptions | platform | draft\|active\|archived |
| plan_price | `app_plan_price` | subscriptions | platform | active\|retired |
| plan_feature | `app_plan_feature` | subscriptions | platform | — |
| addon | `app_addon` | subscriptions | platform | active\|archived |
| subscription | `app_subscription` | subscriptions | organization | trialing\|active\|past_due\|cancelled\|expired |
| subscription_change | `app_subscription_change` | subscriptions | organization | scheduled\|applied\|cancelled |
| subscription_entitlement | `app_subscription_entitlement` | subscriptions | organization | — |
| subscription_addon | `app_subscription_addon` | subscriptions | organization | active\|removed |
| usage_record | `app_usage_record` | subscriptions | organization | — |
| subscription_access_state | `app_subscription_access_state` | subscriptions | organization | full\|limited\|blocked |

**Notes:**
- `app_feature` and `app_addon_price` are NOT separate tables; `feature_code` is embedded in `app_plan_feature` and `app_addon`; `amount/currency/billing_period` on `app_addon` directly.
- Plan statuses: `draft | active | archived` (spec used `published→active`, `retired→archived`).
- **No invoice, payment, billing_profile tables created** (confirmed by test_subscriptions_schema_k1).

**Audit:** reutilizar `app_audit_log` (016/017).

**No crear en 018:** invoice, payment, billing_profile, refund, credit_note, payment_attempt.

---

## Fichas resumidas

### app_plan
PK plan_id · code unique · status draft|published|retired · trial_days_default · audit · KPI catalog

### app_plan_price
PK · FK plan · currency+period+amount · status · snapshot source for subs · KPI MRR (propuesto)

### app_feature / app_plan_feature
Catálogo + mapping limits

### app_addon / app_addon_price
Complementos configurables

### app_subscription
PK · FK org+plan+price · status machine · billing_currency · periods · access_state · activation_source · unique active-set per org (v1)

### app_subscription_change
Append historial · types · scheduled/applied

### app_subscription_entitlement
Feature efectivo · source plan|addon|override

### app_usage_record
Quantity · feature · period · idempotency

---

## Índices lógicos
- plan code/status  
- price (plan, currency, period, active)  
- subscription (org_id, status)  
- entitlement (subscription_id, feature_code)  
- usage (org, feature, period) + idempotency unique  

## Sensibilidad / retención
Catálogo baja; subscription/usage media; retención comercial/financiera prep billing.
