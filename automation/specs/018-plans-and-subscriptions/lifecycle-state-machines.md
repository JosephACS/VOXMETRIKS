# Lifecycle State Machines — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
Cada transición: origen · acción · actor · condición · destino · evento · auditoría · prohibido.

---

## A. Organization (referencia 016 — no redefinir)

`provisioning` · `active` · `suspended_by_platform` · `closed`  
**Prohibido:** past_due / limited como status de org.

---

## B. Plan catalog

| Origen | Acción | Actor | Destino | Evento | Prohibido |
|--------|--------|-------|---------|--------|-----------|
| (none) | create | platform_admin | draft | PlanCreated | — |
| draft | publish | platform_admin | published | PlanPublished | publish sin price |
| published | retire | platform_admin | retired | PlanRetired | hard delete |
| retired | republish | platform_admin | published | PlanRepublished | silencioso |

---

## C. Subscription

| Origen | Acción | Actor | Condición | Destino | Evento | Prohibido |
|--------|--------|-------|-----------|---------|--------|-----------|
| (none) | start_trial | owner/billing_manager | org active; plan trial | trialing | SubscriptionActivated | trial sin org |
| (none) | start_active | owner/billing_manager/orquestación | plan price; source tagged | active | SubscriptionActivated | afirmar paid sin evento |
| trialing | convert | owner/orquestación | policy / PaymentSettled futuro | active | SubscriptionActivated | — |
| trialing | cancel | owner | — | canceled | SubscriptionCanceled | — |
| trialing | expire | sistema | trial_ends_at | expired | SubscriptionExpired | — |
| active | mark_past_due | orquestación | billing fail event | past_due | SubscriptionPastDue | suspender org |
| past_due | recover | orquestación | PaymentSettled | active | SubscriptionRecovered | — |
| past_due | cancel | owner/sistema | policy | canceled | SubscriptionCanceled | — |
| active | schedule_cancel | owner | period end | active + flag | CancelScheduled | — |
| active | cancel_immediate | owner | policy allows | canceled | SubscriptionCanceled | bypass policy |
| * | period_end_cancel | sistema | flag / residual | canceled/expired | SubscriptionCanceled/Expired | — |
| canceled | expire | sistema | residual end | expired | SubscriptionExpired | — |
| expired | resubscribe | owner | new cycle | trialing/active | SubscriptionResubscribed | mutate expired in-place |

---

## D. Access (paralelo)

| Origen | Acción | Señal | Destino | Evento |
|--------|--------|-------|---------|--------|
| * | set_full | activate/recover | full | AccessChanged |
| full | limit | past_due/over-limit | limited | AccessChanged |
| limited | block | gracia agotada | blocked | AccessChanged |
| limited/blocked | restore | PaymentSettled | full | AccessChanged |

---

## E. subscription_change

`pending` → `scheduled` → `applied` | `canceled` | `rejected`
