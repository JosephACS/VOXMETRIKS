> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Plans and Subscriptions

**Feature Branch**: `018-plans-and-subscriptions` *(propuesta; Git manual)*  
**Feature Directory**: `.specify/history/018-plans-and-subscriptions/`  
**Created**: 2026-07-11  
**Status**: **CLOSED_WITH_ACCEPTED_DEBT**  
**Implementation**: **IMPLEMENTATION_COMPLETE**  
**Closed**: 2026-07-11  
**Input**: Tercera capacidad de implementación tras 016 Organizations y 017 CRM (mapa 015 orden 3).  
**Readiness:** Backend package, 4 test suites, frontend package, and docs complete. **K0–K5 DONE.** Formal close: `evidence/spec-closure.md`.

**Número de spec:** **018**.

**Prerrequisitos:** Constitución v2.0.0; 015 `CLOSED_WITH_DEFERRED_DECISIONS`; 016 `CLOSED_WITH_ACCEPTED_DEBT`; 017 `CLOSED_WITH_ACCEPTED_DEBT`.

**feature.json:** avanzado a **019** tras cierre de 018.

---

## Objetivo

Diseñar el dominio **subscriptions**: catálogo de planes, precios configurables, features, entitlements, trial, suscripción org-scoped, cambios, addons, usage, renovación, cancelación, reactivación y **access state** — sin facturar ni cobrar.

```text
organization (016)
→ plan / plan_price / feature
→ entitlement
→ trial | subscription
→ subscription_change / addon / usage
→ renewal / cancellation / reactivation
→ access state (full | limited | blocked)
→ handoff futuro a Billing (019+)
```

---

## Separación obligatoria de lifecycles

| Concepto | Estados | Owner |
|----------|---------|-------|
| **Organization** | provisioning · active · suspended_by_platform · closed | organizations (016) |
| **Subscription** | trialing · active · past_due · canceled · expired | subscriptions (018) |
| **Access** | full · limited · blocked | subscriptions + orquestación (018) |

La **mora** es señal de Billing futuro (`PaymentAttemptFailed` / invoice past_due).  
Subscriptions **consume eventos** y actualiza subscription/access; **no** marca “pagada” por sí misma ni suspende la organización.

---

## Alcance (IN)

- Catálogo configurable de planes (draft/published/retired).
- `plan_price` por moneda y periodo (sin precios definitivos).
- Features, límites, entitlements.
- Trial configurable.
- Subscription org-scoped + cambios (upgrade/downgrade/scheduled).
- Addons y usage records.
- Renovación, cancelación (period-end / immediate por política), vencimiento, reactivación.
- Access state.
- Integración con Organizations (016).
- Handoff documental a Billing.
- APIs/UI/pruebas/KPIs **diseñados**.

---

## Fuera de alcance (OUT)

| Tema | Estado |
|------|--------|
| Invoice / payment / refund / credit note | OUT → Billing |
| Conciliación / PaymentProvider / impuestos | OUT |
| billing_profile fiscal | OUT |
| CRM adicional / campañas / artistas / rights | OUT |
| Afirmar cobro o “subscription paid” sin evento billing | PROHIBIDO |
| SQL / tablas / código | OUT en este borrador |
| Spec 019 | no crear |

---

## Principio de diseño

```text
negocio → OE/OT/OO → capacidades → procesos → actores → CU → reglas → estados
→ datos → backend → frontend → reportes → KPIs → pruebas → evidencia
```

Fuente: Constitución 2.0.0 P0; proceso C 015; golden path pasos 6–7 (+ handoff 8+).

---

## User Stories (documentales)

### US1 — Catálogo de planes (P1)
Como platform_admin, publico planes con features y precios configurables por moneda/periodo.

### US2 — Iniciar suscripción / trial (P1)
Como owner/billing_manager de org active, inicio trial o suscripción referenciando plan_price; se materializan entitlements.

### US3 — Cambiar plan / addon (P1)
Como owner/billing_manager, solicito upgrade/downgrade/addon; queda `subscription_change`; entitlements se recalculan.

### US4 — Usage y límites (P2)
Como sistema, registro usage; si supera límite, access puede pasar a limited vía política (sin inventar cobro).

### US5 — Renovación / cancelación (P1)
Como sistema/owner, renuevo ciclo o cancelo (period-end o immediate si política); emito eventos para Billing.

### US6 — Mora y access (P1)
Como orquestación, al recibir evento financiero fallido → past_due + limited/blocked; al PaymentSettled → recover; **sin** mutar org.status.

### US7 — Reactivación (P2)
Como owner, reactivación crea nuevo ciclo/change auditado — no mutar expired in-place.

### US8 — Handoff Billing (P1 documental)
Publico SubscriptionRenewalDue / EntitlementsChanged sin leer tablas invoice.

---

## Requirements

- **FR-001** Distinguir org / subscription / access lifecycles.
- **FR-002** Plan catalog platform-scoped; subscription org-scoped.
- **FR-003** Una `billing_currency` por subscription; no FX v1.
- **FR-004** Features ⊆ entitlements activos (BR-SUB-01).
- **FR-005** Todo cambio → `subscription_change` (BR-SUB-04).
- **FR-006** No leer tablas internas de billing (BR-SUB-07).
- **FR-007** past_due solo por eventos billing/orquestación — no auto-paid.
- **FR-008** Org suspended/closed bloquea mutaciones de subscription sensibles.
- **FR-009** Trial no factura salvo política futura (BR-SUB-02) — 018 no emite invoice.
- **FR-010** APIs `/api/v1/plans` y `/api/v1/subscriptions` diseñadas.
- **NFR-001** DESIGN ≠ implementado.
- **NFR-002** Precios configurables; no tarifas definitivas.
- **NFR-003** No PAN/CVV; no compliance legal afirmado.

---

## Success Criteria (cierre borrador)

1. Tres lifecycles separados documentados.  
2. Catálogo + pricing + features/entitlements.  
3. Trial/subscription/change/addon/usage/renewal/cancel.  
4. Access state definido.  
5. Handoff Billing sin billing oculto.  
6. Integración Organizations clara.  
7. APIs/UI/pruebas trazadas.  
8. Nada marcado implementado sin serlo.

---

## Artefactos

Ver carpeta: assessment, models, lifecycle, rules, roles, data-model, api-contracts, frontend-flows, billing-handoff, audit, migration, test-strategy, traceability, plan, tasks, checklist.
