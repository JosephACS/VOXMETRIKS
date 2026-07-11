# Implementation Plan: CRM and Commercial Contracting

**Branch**: `017-crm-and-commercial-contracting` *(propuesta)* | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Status**: **DESIGN_APPROVED** (borrador) — **IMPLEMENTATION_PENDING**  
**Código / SQL / feature.json / Constitución / TRACEABILITY-MASTER:** **no** modificados en este borrador.

## Summary

Diseñar el dominio CRM + contrato comercial sales-assisted hasta conversión a Organizations (016). Handoff a subscriptions/billing queda como señal/evento futuro, sin implementación.

## Technical Context (futuro)

| Campo | Valor |
|-------|-------|
| Language | Python 3.12 / TypeScript (Angular) |
| Backend | Futuro `packages/crm` (+ capa contracts comercial o submódulo) |
| Storage | DuckDB `app_*` (académico; mismos límites 016) |
| Auth | Bearer session opaca existente; roles plataforma sales_* |
| Orgs | Reutilizar `packages/organizations` (016) para create/link/invite |
| Testing | pytest + Angular unit + Playwright (diseñado) |
| Constraints | Constitución 2.0.0; deny by default; no billing |

## Constitution Check (documental)

| Gate | Resultado |
|------|-----------|
| Cadena P0 | PASS (docs) |
| No dominio vacío sin spec | PASS (017 es la spec CRM) |
| DESIGN ≠ implementado | PASS |
| Dinero/honestidad | PASS (precios propuestos; sin cobro) |
| Multi-org | PASS (conversión vía 016) |
| feature.json | **sin cambio** (sigue 016) |
| Constitución | **sin cambio** |

## Project Structure (futuro — no crear ahora)

```text
apps/backend/app/packages/crm/            # NUEVO (implementación futura)
apps/frontend/src/app/packages/crm/       # NUEVO (implementación futura)
# organizations / identity: existentes — consumir, no duplicar
```

## Fases futuras de implementación (no autorizadas aún)

| Fase | Contenido | Estado |
|------|-----------|--------|
| D0 | Activación feature.json → 017 + baseline | NOT STARTED |
| D1 | Schema `app_crm_*` + repos | NOT STARTED |
| D2 | Dominio / use cases | NOT STARTED |
| D3 | API platform-scoped + permisos | NOT STARTED |
| D4 | Frontend CRM | NOT STARTED |
| D5 | Conversión ↔ Organizations + seguridad | NOT STARTED |
| D6 | Validación integral y cierre | NOT STARTED |

## Decisiones humanas pendientes

1. **Umbrales de descuento / aprobación** — valores exactos o solo config keys.  
2. **Naming físico** — confirmar `app_crm_prospect` vs variantes (ver `data-model.md`).  
3. **Unificar `lead` vs `new`** en prospect status.  
4. **¿`platform_finance` participa en 017 v1?** (015 lo cita para términos no estándar; actores mínimos 017 no lo listan).  
5. **Owner inicial en conversión** — siempre contacto con user_id; siempre invite 016; o política mixta.  
6. **Prefijo API** — `/api/v1/crm/*` unificado vs `/contracts` separado.  
7. **Probabilidad** — solo manual vs tabla de reglas por stage.  
8. **Monedas permitidas** — whitelist académica.  
9. **Retención PII comercial** — plazos.  
10. **¿Contrato comercial vive en package `crm` o `contracts`?** (015 separó dominios; 017 es una spec de capacidad).

## Risks

| Riesgo | Mitigación documental |
|--------|----------------------|
| Confundir commercial_contract con subscription | Estados y OUT explícitos |
| Crear org fuera de 016 | Conversión solo vía puertos Organizations |
| Billing oculto en quotation | plan_code = referencia conceptual; no activate |
| Acceso org-cliente al CRM | Permisos platform-only; tests aislamiento |
| Doble conversión | `crm_customer_conversion` unique + idempotency |
