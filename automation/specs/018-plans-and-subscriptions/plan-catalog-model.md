# Plan Catalog Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Dominio:** subscriptions · **Scope:** platform

---

## plan

### Propósito
Producto SaaS vendible configurable (no tarifa definitiva).

### Campos
`plan_id` · `code` (único) · `display_name` · `description?` · `status` · `trial_days_default?` · `is_public` · `sort_order` · `created_at` · `updated_at` · `retired_at?`

### Estados
`draft` · `published` · `retired`

| Transición | Actor | Regla |
|------------|-------|-------|
| draft → published | platform_admin | ≥1 plan_price active; ≥1 feature mapping |
| published → retired | platform_admin | no borrar; nuevas subs no lo eligen |
| retired → published | platform_admin | excepción auditada |

### Reglas
| ID | Regla |
|----|-------|
| BR-PLAN-01 | code único global |
| BR-PLAN-02 | Solo `published` seleccionable por org (salvo platform override auditado) |
| BR-PLAN-03 | Retire no elimina historial de subscriptions existentes |
| BR-PLAN-04 | Nombres Starter/Growth/Enterprise = ilustrativos si se usan en seed demo |

### Relación CRM
`plan.code` puede matchear `plan_code` de cotización 017 (HUM010).

### KPI
planes publicados (ops); no inventar adopción.
