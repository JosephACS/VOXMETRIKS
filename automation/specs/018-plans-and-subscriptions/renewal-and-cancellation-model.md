# Renewal and Cancellation Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Renovación

Al acercarse `current_period_end`:

1. Emitir `SubscriptionRenewalDue` (handoff Billing).  
2. **No** crear invoice en 018.  
3. Si Billing futuro confirma ciclo OK → `RenewalCompleted` → extender period + keep `active`.  
4. Si fallo de pago → evento → `past_due` + access degrade.  
5. Sin Billing: modo académico puede “simular” extensión solo con flag demo explícito y audit — **nunca** afirmar cobro real.

## Cancelación

| Modo | Comportamiento |
|------|----------------|
| `cancel_at_period_end` | Flag true; status sigue active/trialing hasta fin periodo → canceled/expired |
| `cancel_immediate` | Solo si política lo permite (HUM002); entitlements cortan según policy |

Siempre: `subscription_change` + `SubscriptionCanceled` + audit.

## Vencimiento
`canceled` → tras residual rights → `expired`.  
`trialing` sin convert → `expired` (o canceled — HUM001).

## Reactivación
No mutar `expired` in-place a active.  
Crear nuevo ciclo (`trialing`/`active`) + change `reactivate` + nuevos entitlements (HUM009).

## Reglas
BR-SUB-03 · BR-SUB-08 heredadas + BR-REN-01 no silent reactivate · BR-REN-02 no org.status change.
