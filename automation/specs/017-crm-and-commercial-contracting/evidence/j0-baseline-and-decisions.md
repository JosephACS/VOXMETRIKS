# J0 — Baseline and decisions

**Date**: 2026-07-11  
**Spec**: 017-crm-and-commercial-contracting

## Preconditions

| Check | Result |
|-------|--------|
| Spec 016 closure | **CLOSED_WITH_ACCEPTED_DEBT** |
| Critical org/auth failures | None blocking |
| feature.json | Updated → `017-crm-and-commercial-contracting` |
| Spec 018 | **Not created** |
| Constitución | **Unchanged** |
| Git | **Not executed** |

## Conservative decisions applied

1. Prospect initial = `new`  
2. API prefix `/api/v1/crm`  
3. Platform-scoped pre-conversion  
4. Roles: sales_agent, sales_manager, platform_admin, auditor  
5. platform_finance OUT  
6. Probability manual 0–100  
7. Single currency; no FX  
8. Discount > 0 requires approval if threshold unset  
9. Academic contract acceptance  
10. Contacts ≠ auto app_user  
11. No real email; claim token returned once  
12. Reuse `app_audit_log`  
13. No silent map of user/admin/engineer → commercial  
14. CRM vs Contracts ownership split  
15. Conversion preserves 016 owner invariant  

## Platform RBAC

**Implemented new** (did not exist as persistent catalog):

- `app_platform_role`
- `app_platform_permission`
- `app_platform_role_permission`
- `app_user_platform_role`

Demo assignments only when `seed_demo_crm_users_enabled`: `sales_agent@voxmetrik.io`, `sales_manager@voxmetrik.io`. Existing demo/admin/engineer **not** granted CRM silently.

## Doc fixes (J0)

- `data-model.md`: `app_commercial_contract` owner = contracts package  
- Applied approved conservative decisions without full editorial rewrite  

## Baseline note

Full gate numbers recorded in J6 evidence. J0 activated tooling + RBAC foundation before schema/use cases.
