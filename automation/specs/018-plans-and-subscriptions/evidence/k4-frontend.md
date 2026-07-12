# K4 — Frontend

**Status**: DONE  
**Test file**: `apps/frontend/src/app/packages/subscriptions/services/subscriptions-k4.spec.ts`  
**Package**: `apps/frontend/src/app/packages/subscriptions/`

## Files created

### Models
- `models/subscriptions.models.ts` — TypeScript interfaces for Plan, PlanPrice, PlanFeature, Addon, Subscription, SubscriptionEntitlement, SubscriptionAddon, UsageRecord, AccessStateInfo, etc.

### Services
- `services/subscriptions-api.service.ts` — Angular HTTP service; sends X-Organization-Id header for org-scoped calls

### Guards
- `guards/subscriptions.guards.ts` — auth guard

### Pages (standalone components, lazy-loaded)
- `pages/plans-catalog.page.ts` — Admin plans catalog
- `pages/plan-detail.page.ts` — Plan detail with prices & features tabs
- `pages/subscription-overview.page.ts` — Org subscription overview + access banner + entitlements
- `pages/trial-start.page.ts` — Trial start form (plan picker, currency)
- `pages/subscription-cancel.page.ts` — Cancel (period_end | immediate)
- `pages/subscription-addons.page.ts` — Addon management
- `pages/subscription-usage.page.ts` — Usage records table

### Routes
- `subscriptions.routes.ts` — SUBSCRIPTIONS_ROUTES lazy-loaded route config

### i18n
- `i18n/en.json` — English strings
- `i18n/es.json` — Spanish strings

## Test coverage (subscriptions-k4.spec.ts)
- listPlans, getPlan, createPlan, activatePlan, archivePlan
- listPlanPrices, setPlanPrice
- listPlanFeatures, configurePlanFeature
- listAddons, createAddon
- listSubscriptions (X-Organization-Id header check)
- startTrial, cancelSubscription, reactivateSubscription
- listEntitlements, listUsage
- addAddon, removeAddon, getAccessState
- Org isolation: different org ids → different headers
