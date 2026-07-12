# Access State Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Estados
`full` · `limited` · `blocked`

Viven en `subscription.access_state` (y opcionalmente por entitlement).

| Estado | Significado |
|--------|-------------|
| full | Entitlements operativos normales |
| limited | Degradación parcial (gracia / over-limit / past_due early) |
| blocked | Bloqueo de features sensibles; org sigue `active` |

## Drivers (orquestación)

| Señal | Access típico |
|-------|---------------|
| trial/active sano | full |
| past_due (billing event) | limited → blocked (política tiempo) |
| PaymentSettled / recover | full |
| over-limit usage | limited (HUM008) |
| org suspended_by_platform | blocked (además de org rules 016) |
| org closed | blocked / no writes |

## Reglas
| ID | Regla |
|----|-------|
| BR-ACC-01 | Access ≠ organization.status |
| BR-ACC-02 | Cambios de access → audit + opcional subscription_change `access_update` |
| BR-ACC-03 | Frontend no es autoridad; backend enforce entitlements+access |
| BR-ACC-04 | No inventar “paid access” sin evento |

## Enforce puntos futuros
Guards API por `feature_code` + access_state; mirror UX banners.
