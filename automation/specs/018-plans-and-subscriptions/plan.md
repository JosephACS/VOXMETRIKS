# Implementation Plan: Plans and Subscriptions

**Branch**: `018-plans-and-subscriptions` *(propuesta)* | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Status**: **IMPLEMENTATION_COMPLETE** — pending J6 formal close by parent  
**Código / DuckDB / feature.json:** feature.json → 018; DuckDB tables created; full implementation K0–K5 complete.

## Summary

Diseñar dominio `subscriptions` sobre Organizations (016). Consumir señales CRM opcionales (`plan_code` / CustomerConverted) sin reabrir CRM. Publicar eventos para Billing futuro. Sin invoice/payment.

## Technical Context (futuro)

| Campo | Valor |
|-------|-------|
| Language | Python 3.12 / TypeScript (Angular) |
| Backend | Futuro `packages/subscriptions` |
| Storage | DuckDB `app_*` (académico; mismos límites 016/017) |
| Auth | Bearer + org RBAC 016 + permisos subscription.* |
| Deps | organizations (016); identity; **no** billing tables |
| Testing | pytest + Angular unit + Playwright (diseñado) |

## Constitution Check (documental)

| Gate | Resultado |
|------|-----------|
| Cadena P0 | PASS (docs) |
| Dinero/honestidad | PASS (precios config; no cobro afirmado) |
| subscriptions ↛ billing tables | PASS (diseño) |
| feature.json | **sin cambio** (sigue 017) |
| Constitución | **sin cambio** |

## Project Structure (futuro — no crear ahora)

```text
apps/backend/app/packages/subscriptions/
apps/frontend/src/app/packages/subscriptions/
```

## Fases futuras (no autorizadas)

| Fase | Contenido | Estado |
|------|-----------|--------|
| K0 | Activar feature.json → 018 + baseline | NOT STARTED |
| K1 | Schema `app_plan*` / `app_subscription*` | NOT STARTED |
| K2 | Dominio / use cases | NOT STARTED |
| K3 | API + entitlements enforce | NOT STARTED |
| K4 | Frontend plan picker + subscription settings | NOT STARTED |
| K5 | Access orchestration + billing event stubs | NOT STARTED |
| K6 | Validación y cierre | NOT STARTED |

## Decisiones humanas pendientes

1. Duración default trial (días) y si trial exige payment method.  
2. Política cancel immediate vs solo period-end en v1.  
3. ¿Una sola subscription activa por org o multi-product? (recomendación: **1 active/trialing/past_due** por org en v1).  
4. Proration upgrade/downgrade: inmediata vs next cycle.  
5. Naming físico `app_plan` vs `app_subscription_plan`.  
6. Quién publica catálogo: solo `platform_admin` o también `platform_finance`.  
7. Usage metering: sync vs async; granularidad diaria.  
8. Access limited: qué features se degradan primero.  
9. Reactivation: ¿mismo subscription_id o nuevo? (recomendación: nuevo ciclo + change; expired row frozen).  
10. Consumo de `plan_code` desde CRM 017: soft-match vs hard validation.

## Risks

| Riesgo | Mitigación |
|--------|------------|
| Confundir paid con active | Explicit: active ≠ paid; paid = billing event |
| Suspender org por mora | Prohibido; solo subscription/access |
| Leer invoices desde subscriptions | BR-SUB-07 + tests |
| Precios “oficiales” inventados | Solo config/seed demo etiquetado |
