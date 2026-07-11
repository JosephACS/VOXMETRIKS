# Migration and Compatibility — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Compatibilidad con 016 / identity

| Área | Expectativa |
|------|-------------|
| Login /me / logout | Intactos |
| Organizations UI/API | Intactos; conversión es **cliente** de 016 |
| Usuarios sin org | Siguen; CRM no los requiere como clientes |
| Permisos org | No otorgan CRM |
| Warehouse ELT | Sin backfill CRM; sin tocar facts |

---

## Migración de datos

| Acción | Política |
|--------|----------|
| Crear tablas `app_crm_*` | Solo en D1 autorizado |
| Backfill prospects desde users/orgs | **No** automático |
| Seeds demo CRM | Solo explícitos `is_demo` / scripts nombrados |
| Borrar datos reales | **Prohibido** para “limpiar” demos |

---

## Coexistencia sales-assisted vs self-service

Self-service (015 alt) puede crear org sin CRM.  
017 no reescribe esas orgs.  
Link mode permite asociar CRM a posteriori con confirmación.

---

## feature.json

Este borrador **no** cambia feature.json (permanece 016).  
Activación 017 = D0 con autorización humana.

---

## Rollback documental

Si NEEDS_CORRECTIONS: corregir docs 017; no tocar código (no hay).
