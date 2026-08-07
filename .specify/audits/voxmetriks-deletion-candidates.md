# VOXMETRIKS — Candidatos a eliminación

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-deletion-candidates.md` |
| **Fecha** | 2026-08-06 |
| **Alcance** | Solo candidatos a **ELIMINAR** (no POSPONER gated) |
| **Estado** | Ninguno eliminado — requiere aprobación + validación |

> **Advertencia:** POSPONER (CRM, billing, royalties, etc.) **no** está en este archivo. Borrar esos módulos sin mapear SQL de reportes es riesgo Alto.

---

## Escala de confianza

| Nivel | Significado |
|-------|------------|
| **Alta** | Sin consumidores detectados en rutas/imports FE o registro BE |
| **Media** | Probable muerto; validar tests dinámicos / imports string |
| **Baja** | Sospecha; no eliminar sin investigación extra |

---

## C1 — Componentes Analytics FE sin ruta

| Campo | Detalle |
|-------|---------|
| **Elemento** | `DashboardComponent`, `TrendingComponent`, `ComparativesComponent`, `AnalyticsComponent` (`analytics/analytics`) |
| **Tipo** | Componentes / páginas FE |
| **Ubicación** | `apps/frontend/src/app/packages/analytics/` |
| **Motivo** | Rutas canónicas redirigen a `/workpanel` o reportes complejos (`CANONICAL_REDIRECTS`, `app.routes.ts`). No hay `loadComponent` hacia estos. |
| **Evidencia** | `nav-access.policy.ts` redirects; explore audit FE §13 |
| **Consumidores encontrados** | Ninguno vía routing; posibles imports estáticos residuales a verificar |
| **Dependencias** | Servicios `stats-*` pueden seguir usándose desde Workpanel/otros — **no borrar APIs** con estos componentes |
| **Consecuencias** | Menos ruido; si alguien bookmarkeaba UI vieja, ya era redirect |
| **Validación** | `rg` imports de cada componente; build FE; navegar `/analytics` → workpanel |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** UI; conservar redirects y servicios backend |

---

## C2 — Shim `features/*`

| Campo | Detalle |
|-------|---------|
| **Elemento** | Re-exports legacy `src/app/features/*` |
| **Tipo** | Módulo FE |
| **Ubicación** | `apps/frontend/src/app/features/` |
| **Motivo** | Solo 3 archivos re-export; `app.routes` no los usa; convención 041 = `packages/` |
| **Evidencia** | packages/README; explore FE |
| **Consumidores** | Ninguno en rutas |
| **Dependencias** | Ninguna funcional |
| **Consecuencias** | Nulas si grep limpio |
| **Validación** | Grep `from '@…/features` / `app/features`; build |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** |

---

## C3 — `SpotifyLinkComponent`

| Campo | Detalle |
|-------|---------|
| **Elemento** | SpotifyLinkComponent |
| **Tipo** | Componente FE |
| **Ubicación** | shared (solo auto-referencia en búsqueda estática) |
| **Motivo** | Sin consumidores |
| **Evidencia** | Explore FE §13 |
| **Consumidores** | Ninguno detectado |
| **Dependencias** | — |
| **Consecuencias** | Nulas |
| **Validación** | Grep selector/class name; build |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** |

---

## C4 — `ReportsTypeTabsComponent`

| Campo | Detalle |
|-------|---------|
| **Elemento** | ReportsTypeTabsComponent |
| **Tipo** | Componente FE |
| **Ubicación** | shared / reports |
| **Motivo** | Comentario indica chrome movido al layout; sin imports |
| **Evidencia** | Explore FE §13 |
| **Consumidores** | Ninguno |
| **Dependencias** | Hub `/reports` actual |
| **Consecuencias** | Nulas si hub intacto |
| **Validación** | Abrir `/reports`; grep |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** |

---

## C5 — `ReportsListPage`

| Campo | Detalle |
|-------|---------|
| **Elemento** | ReportsListPage |
| **Tipo** | Página FE |
| **Ubicación** | `packages/reporting/` |
| **Motivo** | No está en `reporting.routes.ts`; hub la reemplazó |
| **Evidencia** | Explore FE §13 |
| **Consumidores** | Ninguno ruteado |
| **Dependencias** | related-reports-panel y hub **sí** se usan — no tocar |
| **Consecuencias** | Bajas |
| **Validación** | Grep clase; rutas reporting |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** página list legado |

---

## C6 — Guards FE exportados sin uso en rutas

| Campo | Detalle |
|-------|---------|
| **Elemento** | `organizationPermissionGuard`, `subscriptionsAuthGuard` |
| **Tipo** | Guards |
| **Ubicación** | organizations/subscriptions packages |
| **Motivo** | Definidos; no referenciados en `*.routes.ts` |
| **Evidencia** | Explore FE §3 |
| **Consumidores** | Ninguno en route tables |
| **Dependencias** | Otros guards org **sí** se usan |
| **Consecuencias** | Baja; o cablear si era intención |
| **Validación** | Grep symbol; decidir delete vs wire |
| **Confianza** | **Alta** (unused) |
| **Recomendación final** | **ELIMINAR** o documentar+wire en fase seguridad — no dejar zombies |

---

## C7 — Backend `packages/users` shim

| Campo | Detalle |
|-------|---------|
| **Elemento** | `app/packages/users` |
| **Tipo** | Paquete BE |
| **Ubicación** | `apps/backend/app/packages/users/` |
| **Motivo** | Duplicado/shim de `identity`; router vivo es identity; cero imports `app.packages.users` en app |
| **Evidencia** | Explore BE §13; `__init__` re-export |
| **Consumidores** | Posibles tests/docs — verificar |
| **Dependencias** | identity |
| **Consecuencias** | Media si tests importan path viejo |
| **Validación** | `rg packages.users` / `packages/users`; pytest auth |
| **Confianza** | **Alta** (runtime) / validar tests |
| **Recomendación final** | **ELIMINAR** tras green tests |

---

## C8 — Superficie HTTP `/api/v2`

| Campo | Detalle |
|-------|---------|
| **Elemento** | Router `/api/v2` + status stubs |
| **Tipo** | API surface |
| **Ubicación** | `apps/backend/app/api/router.py`, `routes/*`, `_status.py` |
| **Motivo** | Frontend solo usa `/api/v1`; status hardcode `module_status()` |
| **Evidencia** | `environment.apiUrl`; 0 hits FE `/api/v2`; explore BE |
| **Consumidores** | Ninguno en este monorepo FE; **desconocido fuera** |
| **Dependencias** | `app/services`, repositories v2 |
| **Consecuencias** | **Altas** si hay cliente externo/postman académico no versionado |
| **Validación** | Buscar en docs/UML/scripts; deprecar 1 ciclo; luego quitar |
| **Confianza** | **Media** (dentro del repo Alta; fuera desconocido) |
| **Recomendación final** | **NO eliminar en primera limpieza** — marcar deprecado; eliminar en oleada posterior |

---

## C9 — `streaming/routes` re-exports no montados

| Campo | Detalle |
|-------|---------|
| **Elemento** | `packages/streaming/routes/*.py` |
| **Tipo** | Compat adapters |
| **Ubicación** | `apps/backend/app/packages/streaming/routes/` |
| **Motivo** | Re-export catalog; **no** `include_router` en `main.py`; servicios audio **sí** vivos |
| **Evidencia** | Explore BE §13 |
| **Consumidores** | Posibles imports de símbolos |
| **Dependencias** | **No borrar** `streaming/services/audio/*` |
| **Consecuencias** | Media si algo importa routes |
| **Validación** | Grep imports; pytest audio |
| **Confianza** | **Media-Alta** |
| **Recomendación final** | **ELIMINAR** solo archivos routes re-export tras grep; preservar audio |

---

## C10 — `NotImplementedPayload`

| Campo | Detalle |
|-------|---------|
| **Elemento** | Schema `NotImplementedPayload` |
| **Tipo** | Modelo |
| **Ubicación** | `apps/backend/app/models/schemas.py` |
| **Motivo** | No hay rutas 501 que lo usen |
| **Evidencia** | Explore BE §9 |
| **Consumidores** | Posible OpenAPI leftover |
| **Dependencias** | — |
| **Consecuencias** | Nulas |
| **Validación** | Grep nombre |
| **Confianza** | **Media** |
| **Recomendación final** | **ELIMINAR** si grep limpio |

---

## C11 — Import `staffCapabilityGuard` no usado en `app.routes.ts`

| Campo | Detalle |
|-------|---------|
| **Elemento** | Import residual en `app.routes.ts` |
| **Tipo** | Dead import |
| **Ubicación** | `apps/frontend/src/app/app.routes.ts` |
| **Motivo** | Guard se usa en package routes, no en app.routes |
| **Evidencia** | Explore FE §13 |
| **Consumidores** | N/A |
| **Dependencias** | — |
| **Consecuencias** | Nulas (lint) |
| **Validación** | Lint/build |
| **Confianza** | **Alta** |
| **Recomendación final** | **ELIMINAR** import muerto |

---

## Explicitamente NO son candidatos a eliminación (aún)

| Elemento | Por qué no |
|----------|------------|
| CRM / Billing / Royalties / Campaigns / CS / Compliance / Subscriptions UI+API | Spec 038: gated; seeds/reportes/Workpanel pueden depender de tablas |
| Personal-account plans | Mock pero rutas/account pueden usarse; POSPONER |
| Recommendations / smart / ai | Parcialmente útiles; SIMPLIFICAR no borrar |
| `/api/v1` enterprise routers solapados | Requiere consolidación, no delete ciego |
| Tablas `app_crm_*`, `app_invoice*`, etc. | Reportes SQL |
| PocketBase / parquet pipeline | Núcleo engineer |
| Enterprise kit components | Base del design system |

---

## Orden sugerido de borrado (tras aprobación)

1. C11 dead import  
2. C2 features shim  
3. C3 SpotifyLink  
4. C4 ReportsTypeTabs  
5. C5 ReportsListPage  
6. C1 analytics components (+ tests FE asociados)  
7. C6 unused guards (o wire)  
8. C7 packages/users  
9. C9 streaming routes re-exports  
10. C10 NotImplementedPayload  
11. C8 `/api/v2` — **solo después** de deprecación documentada  

Tras cada ítem: build/test del área + smoke demo del rol afectado.

---

## Checklist de validación genérico

```
[ ] Grep nombre símbolo / path en monorepo
[ ] Grep en automation/specs y docs (menciones)
[ ] Build frontend o pytest backend según área
[ ] Smoke rutas relacionadas (redirects siguen OK)
[ ] Confirmar que no se eliminó servicio/API aún usado
[ ] Actualizar este archivo: estado ELIMINADO + fecha (cuando se ejecute)
```

---

**Fin candidatos a eliminación.**  
Ningún archivo funcional ha sido borrado en la fase de auditoría.
