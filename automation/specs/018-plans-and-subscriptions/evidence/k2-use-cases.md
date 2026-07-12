# K2 — Use Cases

**Status**: DONE  
**Test file**: `apps/backend/tests/test_subscriptions_use_cases_k2.py`  
**Source**: `apps/backend/app/packages/subscriptions/application/use_cases.py`

## Implemented use cases

### PlanUseCases
- `CreatePlan` — status starts as `draft`
- `ActivatePlan` — draft → active
- `ArchivePlan` — active → archived

### PlanPriceUseCases
- `SetPlanPrice` — upsert by (plan_id, currency, billing_period); retire old active price for same tuple

### PlanFeatureUseCases
- `ConfigurePlanFeature` — upsert feature_code on plan

### AddonUseCases
- `CreateAddon`, `ArchiveAddon`

### SubscriptionUseCases
- `StartTrial` — requires active plan, trial_days from plan.trial_days_default or request; org uniqueness check (only 1 active/trialing/past_due per org)
- `CreateSubscription` — direct active subscription
- `ActivateSubscription` — trialing → active
- `SchedulePlanChange` — records change_type=plan_change, status=scheduled
- `ApplyPlanChange` — applies scheduled change, evaluates entitlements
- `CancelSubscription` — `period_end` (sets cancel_at_period_end) or `immediate` (status=cancelled)
- `ReactivateSubscription` — cancelled/expired → active
- `RenewSubscription` — advances period dates, reactivates past_due if needed
- `UpdateAccessState` — updates access_state, reason; also mirrors on subscription row; `stub_billing_hook` for 019

### SubscriptionAddonUseCases
- `AddSubscriptionAddon`, `RemoveSubscriptionAddon`

### UsageUseCases
- `RecordUsage` — idempotency via idempotency_key
- `EvaluateEntitlements` — rebuilds entitlements from plan features + active addons

## Business rules enforced

- One active/trialing/past_due subscription per org max
- `past_due` only via `UpdateAccessState`
- Subscription never marked "paid"
- `organization_id` required (raises `OrganizationRequiredError` if missing)
- Trial days from plan.trial_days_default (or request override), no magic constants
- Parameterized SQL throughout, pagination on list queries
- Audit log via `app_audit_log` for plan lifecycle actions
