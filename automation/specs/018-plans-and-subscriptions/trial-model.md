# Trial Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Propósito
Periodo de evaluación configurable **sin emitir invoice** en 018.

## Campos / comportamiento
- `status = trialing`
- `trial_ends_at` obligatorio
- `activation_source = trial`
- Entitlements = plan features (pueden ser subset “trial” si se define — HUM)

## Reglas
| ID | Regla |
|----|-------|
| BR-TRIAL-01 | Solo si plan permite trial (`trial_days_default` o override) |
| BR-TRIAL-02 | No factura / no payment_attempt en 018 (BR-SUB-02) |
| BR-TRIAL-03 | Al expirar sin convert → `expired` o política a `canceled` (elegir HUM001) |
| BR-TRIAL-04 | Convert a `active` en 018 = **manual/orquestación académica** o espera `PaymentSettled` futuro — documentar source |
| BR-TRIAL-05 | Cancel trial → `canceled` con change auditado |

## Honestidad UI
Etiquetar “periodo de prueba — sin cobro automático en esta versión académica”.
