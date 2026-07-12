# Current System Assessment — Spec 018

**Status**: Diseñado (assessment) · IMPLEMENTATION_PENDING  
**Fecha**: 2026-07-11

---

## Qué existe hoy

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Identity | Implementado | 016 |
| Organizations / members / RBAC org | Implementado | 016 CLOSED_WITH_ACCEPTED_DEBT |
| CRM + commercial contract + conversion | Implementado | 017 CLOSED_WITH_ACCEPTED_DEBT |
| `plan_code` en cotización CRM | Referencia conceptual | 017 — no valida plan publicado |
| Platform RBAC sales_* | Implementado | 017 |
| Plan catalog / subscription / entitlements | **No implementado** | sin package `subscriptions` |
| Billing / invoice / payment | Diseñado 015 | OUT 018 |
| `billing_manager` org role | Sembrado en 016 catalog | sin permisos subscription aún |

---

## Contradicciones / tensiones

1. **017 `plan_code`** no exige plan publicado — 018 debe definir soft vs hard validation (HUM010).  
2. **016 `billing_manager`** existe como rol org pero sin dominio billing/subscription implementado — 018 asignará permisos subscription.*; billing.* quedan futuros.  
3. **CustomerConverted** (017) no activa plan — 018 debe aceptar handoff opcional sin auto-subscribe silencioso.  
4. **Enterprise analytics** actual ≠ SaaS MRR — no reutilizar como billing truth.  
5. **DuckDB** no es ledger ni motor de billing — límites académicos.  
6. **Identity role `admin`** ≠ platform catalog admin — no bypass.  
7. **015** ilustra Starter/Growth/Enterprise — **no** son precios oficiales; solo ejemplos.  
8. Evento `SubscriptionActivated` en 015 cubre trial y paid — 018 debe etiquetar `activation_source` (`trial`|`manual`|`billing_event`) para honestidad.

---

## Reutilización obligatoria

| Componente | Uso |
|------------|-----|
| Organizations active + owner | Precondición subscription |
| Org permissions pattern | Extender códigos `subscription.*` / `plan.*` |
| Audit log (`app_audit_log`) | Mutaciones sensibles |
| CRM conversion event (opcional) | Semilla de plan sugerido |

## No reutilizar

| Anti-patrón | Por qué |
|-------------|---------|
| Marcar subscription paid sin PaymentSettled | Honestidad dinero |
| Suspender org por past_due | BR-ORG-05 |
| Tablas invoice en package subscriptions | BR-SUB-07 |
| Auto-crear subscription en conversión CRM | Debe ser explícito |

---

## Baseline honesto

```text
subscriptions = DESIGN_APPROVED / IMPLEMENTATION_PENDING
organizations = IMPLEMENTATION_COMPLETE (016)
crm/contracts = IMPLEMENTATION_COMPLETE (017)
billing = DESIGN_APPROVED (015) / OUT 018
```
