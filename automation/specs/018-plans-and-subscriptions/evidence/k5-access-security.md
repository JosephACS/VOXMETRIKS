# K5 — Access State & Security

**Status**: DONE  
**Test file**: `apps/backend/tests/test_subscriptions_security_k5.py`

## Access State

- `app_subscription_access_state` table tracks `full | limited | blocked` per subscription.
- `UpdateAccessState` use case updates both the access_state table and mirrors the value on the subscription row for query convenience.
- `stub_billing_hook(subscription_id, event, payload)` is a stub callable — logs the event for 019 orchestration.
- `past_due` status only set via `UpdateAccessState` (orchestration hook), never by subscription logic itself.

## Security tests (test_subscriptions_security_k5.py)

- 401 for unauthenticated access to all subscription endpoints
- 403 for insufficient permissions (missing subscription.view, subscription.create, etc.)
- Absence of billing/invoice/payment endpoints (404 probe)
- Organization isolation: org A cannot see org B subscriptions
- `past_due` can only be triggered via UpdateAccessState, not by any standard create/activate/trial flow
- Platform permissions deny by default: user without plan.create cannot create plans

## Permissions model

### Platform (plan catalog)
| Permission | platform_admin | auditor |
|------------|---------------|---------|
| plan.view | ✓ | ✓ |
| plan.create | ✓ | — |
| plan.activate | ✓ | — |
| plan.archive | ✓ | — |
| plan_price.manage | ✓ | — |
| plan_feature.manage | ✓ | — |
| addon.manage | ✓ | — |

### Organization (subscriptions)
| Permission | owner | administrator | billing_manager |
|------------|-------|--------------|-----------------|
| subscription.view | ✓ | ✓ | ✓ |
| subscription.create | ✓ | ✓ | ✓ |
| subscription.change | ✓ | ✓ | ✓ |
| subscription.cancel | ✓ | ✓ | ✓ |
| subscription.reactivate | ✓ | — | ✓ |
| usage.view | ✓ | ✓ | ✓ |
