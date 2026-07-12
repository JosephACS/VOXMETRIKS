# Test Strategy (diseño) — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Capas futuras
Unit dominio · repos · use cases · API authz · access enforce · FE unit · E2E · compat 016/017

## Casos obligatorios

1. Org closed/suspended → no create subscription.  
2. Publish plan sin price → reject.  
3. Select retired plan → 410.  
4. Trial create → entitlements; no invoice table touch.  
5. Dual active subscription → 409 (si política single).  
6. Change upgrade → subscription_change applied + entitlements.  
7. Cancel period-end vs immediate policy.  
8. past_due via orchestration event → access limited; org still active.  
9. PaymentSettled → recover; no org status flip.  
10. Over-limit usage → limited (policy).  
11. Cross-org IDOR → 403/404.  
12. Org member without permission → 403.  
13. Platform publish permission.  
14. Reactivate expired → new cycle not in-place mutate.  
15. Subscriptions package never SELECTs app_invoice* (guard test).  
16. activation_source required.  
17. Currency mismatch addon vs sub → 422.  
18. CRM handoff does not auto-create subscription.

## Golden path E2E (diseñado)
login owner → org active → pick plan → start trial → entitlements visible → schedule change → cancel at period end → audit.  
Billing path stubbed/not run.

## KPIs en pruebas
Solo fixtures; no assert MRR de producción inventado.
