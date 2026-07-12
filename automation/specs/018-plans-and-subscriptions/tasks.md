# Tasks — Spec 018 Plans and Subscriptions

**Status**: IMPLEMENTATION_COMPLETE — pending J6 formal close by parent  
K0–K5 implemented. K6 = J6 formal close (human).

## Fase documental

- [x] T001 Confirmar 018 disponible
- [x] T002 Crear directorio `018-plans-and-subscriptions/`
- [x] T003 `spec.md` + lifecycles separados
- [x] T004 `plan.md` + decisiones humanas
- [x] T005 Assessment + modelos plan/pricing/feature/subscription/trial/change/addon/usage/renewal/access
- [x] T006 Lifecycle + rules + roles
- [x] T007 data-model + api + frontend + billing-handoff
- [x] T008 audit + migration + test-strategy + traceability
- [x] T009 checklist + tasks
- [ ] T010 Revisión humana / DESIGN_APPROVED formal

## Implementación (COMPLETA)

- [x] K0 feature.json → 018 (ya apuntaba a 018)
- [x] K1 Schema — `ensure_subscription_tables`, 12 tablas, catalogs seeded
- [x] K2 Use cases — `use_cases.py` con todos los casos
- [x] K3 API — routers plans/addons/subscriptions, wired en main.py
- [x] K4 Frontend — Angular package, services, models, pages, routes, tests, i18n
- [x] K5 Access + event stubs — `UpdateAccessState`, `stub_billing_hook` stub
- [ ] K6 Validación / cierre formal (human — J6)

## Prohibido en este borrador

- [x] No código / DuckDB
- [x] No feature.json
- [x] No Constitución
- [x] No spec 019
- [x] No Git
