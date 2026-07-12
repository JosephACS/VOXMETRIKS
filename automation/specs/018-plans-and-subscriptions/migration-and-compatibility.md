# Migration and Compatibility — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Compatibilidad

| Área | Expectativa |
|------|-------------|
| Identity / orgs / CRM | Intactos |
| Org sin subscription | Permitido (como user sin org fue permitido en 016) |
| CRM plan_code | Soft link hasta HUM010 |
| Warehouse ELT | Sin backfill subscriptions |
| feature.json | Sigue 017 hasta K0 |

## Migración de datos

| Acción | Política |
|--------|----------|
| Crear tablas app_plan* / app_subscription* | Solo K1 autorizado |
| Backfill subs desde orgs | **No** automático |
| Seed planes demo | Explícito + etiquetado |
| Borrar datos reales | Prohibido para “limpiar” |

## Coexistencia caminos
- Sales-assisted (017) → org → **elige plan en 018** (no auto).  
- Self-service futuro → org → plan → (billing) — 018 soporta create subscription; checkout OUT.

## Rollback documental
NEEDS_CORRECTIONS → corregir docs; no hay código.
