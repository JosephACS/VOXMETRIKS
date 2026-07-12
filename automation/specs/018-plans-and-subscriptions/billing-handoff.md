# Billing Handoff — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Billing implementation = OUT (futura spec).**

---

## Principio (015)

```text
subscriptions publica eventos de ciclo/consumo
  → billing consume y genera invoice/payment
  → billing publica PaymentSettled / PaymentAttemptFailed
  → orquestación actualiza subscription status / access
subscriptions NO lee tablas invoice/payment
```

---

## Eventos publicados por 018 (conceptuales)

| Evento | Cuándo | Payload mínimo |
|--------|--------|----------------|
| `PlanSelected` | create sub | org, plan, price snapshot |
| `SubscriptionActivated` | trial/active start | org, sub, source |
| `EntitlementsChanged` | materialize/change | feature deltas |
| `SubscriptionRenewalDue` | near period end | org, sub, amount snapshot, currency |
| `UsageRecorded` | usage ingest (billable flag?) | feature, qty |
| `SubscriptionCanceled` | cancel | mode, at |
| `SubscriptionPastDue` | after billing fail signal | org, sub |
| `SubscriptionRecovered` | after PaymentSettled | org, sub |
| `RenewalCompleted` | after successful cycle signal | new period |

## Eventos consumidos (futuros)

| Evento | Efecto en 018 |
|--------|----------------|
| `PaymentSettled` | recover past_due → active; convert trial policy; extend period |
| `PaymentAttemptFailed` | mark past_due + access limited |
| `InvoicePastDue` | same family signal |
| `CustomerConverted` (017) | opcional sugerir plan — **no** auto-subscribe |

---

## Contrato de handoff

Billing futuro necesita:
- organization_id  
- subscription_id  
- billing_currency  
- price_amount_snapshot + period  
- customer legal refs (from org / CRM contract) — **read via org**, not CRM write  

018 **no** crea `billing_profile`; solo documenta dependencia.

## Anti-patrones
- Embedding invoice rows in subscriptions package  
- Setting status=active because “user clicked pay” without provider  
- Suspending organization on failed payment  
