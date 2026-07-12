# K1 — Schema

**Status**: DONE  
**Test file**: `apps/backend/tests/test_subscriptions_schema_k1.py`

## Tables created (all via CREATE IF NOT EXISTS in ensure_subscription_tables)

1. `app_plan` — status: draft|active|archived, trial_days_default
2. `app_plan_price` — plan_id FK, currency, billing_period, amount, status: active|retired
3. `app_plan_feature` — plan_id FK, feature_code, limit_value, enabled
4. `app_addon` — code unique, feature_code, display_name, status, optional amount/currency/billing_period
5. `app_subscription` — organization_id required, plan_id FK, status machine, billing_currency, access_state mirror
6. `app_subscription_entitlement` — subscription_id FK, feature_code, source: plan|addon|override
7. `app_subscription_change` — subscription_id FK, change_type, from_plan_id, to_plan_id, status
8. `app_subscription_addon` — subscription_id FK, addon_id FK, status: active|removed
9. `app_usage_record` — subscription_id FK, feature_code, quantity, period, idempotency_key
10. `app_subscription_access_state` — subscription_id FK, access_state: full|limited|blocked, reason

## RBAC seeding

- Platform permissions added to `platform_rbac/infrastructure/catalogs.py`:
  - `plan.view`, `plan.create`, `plan.activate`, `plan.archive`, `plan_price.manage`, `plan_feature.manage`, `addon.manage`
  - Granted to `platform_admin` and `auditor` (view only)
- Org permissions added to `organizations/infrastructure/catalogs.py`:
  - `subscription.view`, `subscription.create`, `subscription.change`, `subscription.cancel`, `subscription.reactivate`, `usage.view`
  - Granted to `owner`, `administrator`, `billing_manager`

## NOT created (verified)

- `invoice`, `payment`, `billing_profile`, `refund`, `credit_note`, `payment_attempt`
