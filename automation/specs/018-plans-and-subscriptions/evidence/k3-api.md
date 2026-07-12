# K3 — API

**Status**: DONE  
**Test file**: `apps/backend/tests/test_subscriptions_api_k3.py`  
**Source**: `apps/backend/app/packages/subscriptions/presentation/`

## Endpoints (wired in main.py under /api/v1)

### Plans (platform-scoped, prefix /plans)
- `GET    /api/v1/plans` — list plans (plan.view)
- `POST   /api/v1/plans` — create plan (plan.create)
- `GET    /api/v1/plans/{plan_id}` — get plan (plan.view)
- `POST   /api/v1/plans/{plan_id}/activate` — (plan.activate)
- `POST   /api/v1/plans/{plan_id}/archive` — (plan.archive)
- `GET    /api/v1/plans/{plan_id}/prices` — (plan.view)
- `POST   /api/v1/plans/{plan_id}/prices` — (plan_price.manage)
- `GET    /api/v1/plans/{plan_id}/features` — (plan.view)
- `POST   /api/v1/plans/{plan_id}/features` — (plan_feature.manage)

### Addons (platform-scoped, prefix /addons)
- `GET    /api/v1/addons` — list addons (plan.view)
- `POST   /api/v1/addons` — create addon (addon.manage)
- `GET    /api/v1/addons/{addon_id}` — get addon (plan.view)
- `POST   /api/v1/addons/{addon_id}/archive` — (addon.manage)

### Subscriptions (org-scoped via X-Organization-Id, prefix /subscriptions)
- `GET    /api/v1/subscriptions` — list (subscription.view)
- `POST   /api/v1/subscriptions/trial` — start trial (subscription.create)
- `POST   /api/v1/subscriptions` — create (subscription.create)
- `GET    /api/v1/subscriptions/{sub_id}` — get (subscription.view)
- `POST   /api/v1/subscriptions/{sub_id}/activate` — (subscription.change)
- `POST   /api/v1/subscriptions/{sub_id}/change` — schedule plan change (subscription.change)
- `POST   /api/v1/subscriptions/{sub_id}/cancel` — (subscription.cancel)
- `POST   /api/v1/subscriptions/{sub_id}/reactivate` — (subscription.reactivate)
- `POST   /api/v1/subscriptions/{sub_id}/renew` — (subscription.change)
- `GET    /api/v1/subscriptions/{sub_id}/entitlements` — (subscription.view)
- `POST   /api/v1/subscriptions/{sub_id}/entitlements/evaluate` — (subscription.change)
- `GET    /api/v1/subscriptions/{sub_id}/addons` — (subscription.view)
- `POST   /api/v1/subscriptions/{sub_id}/addons` — (subscription.change)
- `DELETE /api/v1/subscriptions/{sub_id}/addons/{addon_id}` — (subscription.change)
- `POST   /api/v1/subscriptions/{sub_id}/usage` — record usage (subscription.change)
- `GET    /api/v1/subscriptions/{sub_id}/usage` — list usage (usage.view)
- `GET    /api/v1/subscriptions/{sub_id}/access-state` — (subscription.view)
- `POST   /api/v1/subscriptions/{sub_id}/access-state` — (subscription.change)

## NOT exposed
- No `/invoice`, `/payment`, `/billing` endpoints
- Verified by test_subscriptions_api_k3 absence checks
