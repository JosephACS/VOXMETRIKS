# Traceability — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

Cadena: 015 proceso C → capacidad 018 → actores → US → reglas → estados → entidades → (API/UI/test futuros) → evidencia futura.

---

## Mapa

| Eslabón | Artefacto |
|---------|-----------|
| Objetivo 015 | SaaS plan → subscription → entitlements |
| Capacidad | Plans & subscriptions (018) |
| Prereqs | 016 orgs · 017 CRM handoff opcional |
| Proceso | operational-model C |
| Actores | role-and-permission-model.md |
| US | spec.md US1–US8 |
| Reglas | business-rules.md |
| Estados | lifecycle-state-machines.md |
| Entidades | data-model.md |
| API | api-contracts.md (diseñado) |
| UI | frontend-flows.md (diseñado) |
| Billing | billing-handoff.md |
| Pruebas | test-strategy.md |
| Evidencia | FUTURO K6 |

---

## US → docs

| US | Modelos clave |
|----|---------------|
| US1 Catalog | plan-catalog, pricing, feature |
| US2 Start/trial | subscription, trial, entitlement |
| US3 Change | subscription-change, addon |
| US4 Usage | usage, access |
| US5 Renew/cancel | renewal-and-cancellation |
| US6 Mora/access | access-state, billing-handoff |
| US7 Reactivate | renewal-and-cancellation |
| US8 Handoff | billing-handoff |

---

## KPIs (propuestos — sin resultados)

Alineados KPI-SAAS-01…09 de 015: gross/net MRR, ARR, logo/revenue churn, renewal, expansion, ARPA, delinquent — madurez **Propuesto**; dependen precios config + (MRR neto) eventos billing futuros.

Limitaciones: sin price → excluir línea; paying_orgs=0 → N/D; no inventar series.

---

## Gaps OK en borrador
Repo/API/UI/test sin implementación.

## Anti-gaps
Endpoint sin permiso · pantalla billing de cobro · tabla invoice · regla sin prueba futura.
