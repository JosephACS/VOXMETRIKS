# API Contracts (diseño) — Spec 018

**Status**: DESIGN_APPROVED · **IMPLEMENTATION_PENDING**  
**Base:** `/api/v1` · Auth Bearer · **No implementado.**

---

## Códigos HTTP
401 · 403 · 404 · 409 (conflict status/unique) · 410 (retired plan) · 422 validation

Idempotency-Key: POST subscription create, changes, usage ingest.

---

## Plans (platform catalog)

| Method | Path | Permiso |
|--------|------|---------|
| GET | `/plans` | plan.view / public published list |
| GET | `/plans/{id}` | plan.view |
| POST | `/plans` | plan.create |
| PATCH | `/plans/{id}` | plan.create |
| POST | `/plans/{id}/publish` | plan.publish |
| POST | `/plans/{id}/retire` | plan.retire |
| GET/POST | `/plans/{id}/prices` | plan_price.manage |
| GET | `/features` | plan.view |
| GET/POST | `/addons` | addon.manage |

Public org users: GET published plans only.

---

## Subscriptions (org-scoped)

Header/context: `X-Organization-Id` (016 pattern).

| Method | Path | Permiso |
|--------|------|---------|
| GET | `/subscriptions` | subscription.view |
| POST | `/subscriptions` | subscription.create | body: plan_price_id, trial? |
| GET | `/subscriptions/{id}` | view |
| POST | `/subscriptions/{id}/change` | subscription.change |
| POST | `/subscriptions/{id}/cancel` | subscription.cancel | body: mode period_end\|immediate |
| POST | `/subscriptions/{id}/reactivate` | subscription.reactivate |
| GET | `/subscriptions/{id}/changes` | view |
| GET | `/subscriptions/{id}/entitlements` | entitlement.view |
| GET/POST | `/subscriptions/{id}/usage` | usage.view / record |

### Past due / recover
**No** endpoint “mark paid”.  
Internal/orquestación: consumir eventos billing (futuro) → service methods.  
Stub académico opcional bajo platform_admin + audit + flag demo — nunca default.

---

## Errores de dominio
- Org not active → 409/422  
- Plan retired → 410  
- Second active subscription → 409  
- Cancel immediate forbidden → 403/422  
- Feature denied → 403  

---

## Fuera de API 018
`/invoices` · `/payments` · `/billing/*` · PaymentProvider webhooks
