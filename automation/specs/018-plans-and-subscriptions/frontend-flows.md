# Frontend Flows (diseño) — Spec 018

**Status**: DESIGN_APPROVED · **IMPLEMENTATION_PENDING**  
Sin billing UI de cobro.

---

## Navegación propuesta

```text
/app/organizations/:id/subscription     → overview + access banner
/app/organizations/:id/subscription/plans → plan picker
/app/organizations/:id/subscription/change → change wizard
/app/organizations/:id/subscription/usage → usage vs limits
/app/platform/plans                     → catalog admin (platform)
/app/platform/plans/:id/prices          → price editor
```

Guards: organizationRequired + subscription.* permissions; platform catalog separado.

---

## Pantallas

### Subscription overview
Status badge (trialing/active/past_due/…) · access_state · period dates · plan name · CTA change/cancel.  
Copy: “El estado active no implica cobro confirmado sin Billing.”

### Plan picker
Lista published plans + prices by currency/period · trial CTA · sin checkout de tarjeta.

### Change wizard
Upgrade/downgrade/addon · scheduled vs immediate · confirmation · no proration money UI definitiva.

### Cancel flow
Period-end default · immediate only if allowed · reason.

### Usage
Bars vs limits · over-limit warning.

### Platform catalog admin
CRUD draft/publish/retire · prices · features · addons · demo labels.

### Access banners
limited/blocked messaging; link a billing futuro “próximamente” sin fake pay.

---

## OUT UI
Invoice list · payment methods · refunds · tax · CRM · campaigns.
