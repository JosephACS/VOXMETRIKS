# VOXMETRIKS — Respuesta al debate de alcance (segunda revisión crítica)

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/decisions/voxmetriks-scope-debate-response.md` |
| **Fecha** | 2026-08-06 |
| **Tipo** | Debate de arquitectura y alcance — **sin cambios de código** |
| **Entrada** | Propuesta de narrativa + menús mínimos + módulos a posponer |
| **Auditoría previa** | `.specify/audits/*` |

> Esta respuesta **no acepta automáticamente** la propuesta. Cada decisión se confronta con evidencia de rutas, guards, servicios, endpoints y datos.

---

## 1. Resumen de postura

**Acuerdo mayoritario con la narrativa**  
`música → actividad → analítica → reportes → ELT → warehouse` es coherente, defendible y superior a pretender el B2B SaaS completo (015) en la demo visible.

**Desacuerdo parcial, no total, con posponer Organizations / Publishing / Rights / Artist Profiles**  
- Sí: **sacar del menú producto** (reducen claridad).  
- No: tratarlos como “irrelevantes” o apagar la **infraestructura** de organización.  
- Motivo: el shell hidrata `OrganizationContextService` para todo usuario autenticado; Workpanel envía `X-Organization-Id` si hay org activa; **la mayoría de simple reports son `org_scoped=True`** y fallan con 400 sin header; Publishing/Rights **sí** exigen `organizationRequiredGuard`.

**Corrección a la auditoría original**  
Clasificar Organizations/Publishing/Rights como “necesarios visibles para admin MVP” fue correcto bajo narrativa B2B 038–041, pero **excesivo** bajo la nueva narrativa musical+analytics+ELT. Se revisa: pasan a **OCULTO PERO FUNCIONAL / POSPONER UI**, no a eliminación.

**Catálogo admin: la propuesta nueva es necesaria y corrige un hueco**  
Hoy el ítem de menú “Catálogo” apunta a `/catalog` (**publishing hub**, org-gated), **no** a `/tracks|/artists|/genres`. Si se ocultan Organizations+Publishing sin redefinir Catálogo, el admin **pierde** la superficie steward del warehouse. El Catálogo mínimo debe ser explícitamente warehouse: canciones/artistas/géneros.

---

## 2. Puntos de acuerdo

| Propuesta | Veredicto | Motivo breve |
|-----------|-----------|--------------|
| Narrativa música + analítica + ELT | **De acuerdo** | Alineada a flujos COMPLETE verificados |
| Menú usuario (Discover…Settings) | **De acuerdo** | Coincide con núcleo listener E2E |
| Fusionar `/history` + `/activity` → Actividad | **De acuerdo** | Duplicación UX real |
| Perfil dentro de `/settings` | **De acuerdo** | `/users` y Settings solapan |
| Recomendaciones dentro de Discover; quitar página | **De acuerdo** | Smart rails ya en home; `/recommendations` es secundaria |
| Quitar `/audio-features` de superficie user | **De acuerdo** | Ya en `LISTENER_HIDDEN_MUSIC_PATHS` |
| Smart/AI solo con etiqueta honestidad | **De acuerdo** | Provider mock / reglas locales |
| Data Ops = ELT + Explorer (nav única) | **De acuerdo** | Misma historia pedagógica |
| Posponer CRM/Billing/Royalties/Campaigns/CS/Compliance/Subs/BA/Business Decisions/Personal billing | **De acuerdo** | Ya `OUT_OF_PRODUCT` / demos |
| Platform Ops fuera de nav primario | **De acuerdo** | Ya `HIDDEN_PRIMARY_OPS_PATHS` |
| Design system: enterprise-* + música listener | **De acuerdo** (no implementar aún) | Kit existente |
| Primera limpieza solo código muerto listado | **De acuerdo con matices** | Ver §9; shim users = CAUTION |
| No borrar `/api/v2`, tablas enterprise, audio vivo | **De acuerdo** | Dependencias / riesgo |

---

## 3. Puntos de desacuerdo (y matices fuertes)

### D1 — “Organizations se puede retirar del flujo visible sin más”

**Desacuerdo parcial.**  
Retirar **CRUD/menú** sí. Retirar **contexto de organización** no.

**Evidencia**
- Shell: `DashboardLayoutComponent` inyecta `OrganizationContextService` y bloquea outlet hasta `ensureReady()` (hidratación para **todos** los autenticados).
- Workpanel FE: `workpanel-api.service.ts` añade `X-Organization-Id` si hay `organizationId`.
- Workpanel BE: org **opcional** (`workpanel/router.py`); sin header funciona con métricas platform/global.
- Simple reports: si `report.org_scoped` y no hay header → **HTTP 400** (`simple_reports/presentation/dependencies.py` líneas 54–59). En `registry.py`, la gran mayoría de informes tienen `org_scoped=True` (~16 True vs ~2 False en flags encontrados).
- Publishing/Rights/Artist-profiles: `organizationRequiredGuard` en sus `*.routes.ts`.

**Qué se pierde al ocultar solo el menú:** poco, si se mantiene auto-selección de org demo.  
**Qué se rompe si se elimina el contexto:** reportes org-scoped, métricas org del Workpanel, deep-links publishing.

**Recomendación:** OCULTO PERO FUNCIONAL + **org demo auto-seleccionada** en seed para staff; sin UI CRUD en menú.

---

### D2 — “Catálogo admin = canciones/artistas/géneros” vs hub actual `/catalog`

**De acuerdo con el objetivo; en desacuerdo con asumir que ya es así.**

**Evidencia**
- Nav admin: sección `catalogHub` → path `/catalog`, label “Catálogo y publicación” (`dashboard-layout.component.ts` ~368–375; i18n `nav.catalogHub`).
- `/catalog` usa `organizationRequiredGuard` + módulo operational (`catalog-publishing.routes.ts`).
- `/tracks`, `/artists`, `/genres` **no** usan org; steward vía `require_admin_user` / interceptor FE.
- Visibilidad menú `catalogHub` exige `hasOrg && canOrg('operational'|…)`.

**Implicación:** al posponer Organizations+Publishing, hay que **redefinir** el ítem Catálogo hacia warehouse. Si solo se ocultan secciones actuales, admin se queda sin Catálogo útil.

**Catálogo mínimo propuesto (veredicto):**
| Ruta | Operación real | Notas |
|------|----------------|-------|
| `/tracks` | Listar, detalle, update/delete admin | **POST create → siempre 403** (ELT-owned) — no inventar “Crear canción” como CRUD completo |
| `/artists` | CRUD catalog artists | Distinto de `/artist-profiles` |
| `/genres` | CRUD géneros | |
| Covers / audio-source | Lectura + repair engineer | No publishing cycle |

**No incluir en Catálogo visible v1:** `/catalog`, `/catalog-review`, `/artist/*` portal, `/catalog-rights/*`, `/artist-profiles/*`.

---

### D3 — Publishing / Rights / Artist Profiles “indispensables” (auditoría original) vs “al roadmap” (nueva propuesta)

**Reviso a favor de la nueva propuesta para superficie visible.**  
No son indispensables para demostrar la narrativa música→analytics→ELT.

| Pregunta | Respuesta con evidencia |
|----------|-------------------------|
| ¿Indispensables para demo core? | **No** |
| ¿Pueden quedar ocultos pero funcionales? | **Sí** — rutas viven; faltaría meterlos en `OUT_OF_PRODUCT` / `DEMO_SECTION` o equivalente (hoy están en `PRODUCT_FINAL_SECTION_IDS`) |
| ¿Solo quitar menú afecta permisos? | Menú: no. Deep-link: siguen accesibles si no se añade `productSurfaceGuard` (hoy **no** llevan product-surface; solo org guards) |
| ¿Catálogo básico sin publishing? | **Sí** — warehouse dims + `/tracks` |
| ¿Riesgo demo? | Bajo si no se promete “ciclo de publicación”; medio si el guión de defensa aún menciona publishing 031 |

**Pérdida al ocultar:** historia B2B “sello publica → review → rights”. Aceptable bajo nueva narrativa.

---

### D4 — Menú admin sin Organizations es “técnicamente limpio”

**Desacuerdo si se interpreta como “admin nunca necesita org”.**  
**Acuerdo** si se interpreta como “admin no gestiona orgs en la demo corta”.

Workpanel y muchos reportes **mejoran o requieren** org context. Solución: bootstrap silencioso, no menú.

---

### D5 — Default post-login admin

**Matiz.**  
Shell redirige `''` → `/discover` para todos. Staff tiene Workpanel en menú principal, pero aterrizaje puede ser Discover. Para la narrativa admin, el **home semántico** debe ser Workpanel; hoy no es redirect automático. No es bloqueante; es deuda de UX a decidir (pregunta humana §11).

---

### D6 — Primera limpieza: `packages/users` como “inmediata”

**Desacuerdo leve.** Runtime muerto, pero `tests/test_packages_d2.py` y `pyproject.toml` lo referencian → **NEEDS CAUTION**, no delete ciego en el mismo commit sin ajustar tests.

---

## 4. Debate detallado: Organizations / Publishing / Rights / Artist Profiles

### 4.1 ¿Organizations es dependencia técnica obligatoria?

| Consumidor | ¿Obligatoria? | Evidencia |
|------------|---------------|-----------|
| Catálogo warehouse `/tracks|/artists|/genres` | **No** | Sin org header; auth admin en writes |
| Workpanel | **No** (opcional) | Header opcional; métricas platform/global |
| Complex reports | **No** (filtro opcional) | Router complex |
| Simple reports `org_scoped` | **Sí para esos informes** | 400 sin `X-Organization-Id` |
| Publishing / Rights / Artist profiles | **Sí** | `organizationRequiredGuard` |
| Shell listener | **Infra sí / UI no** | `ensureReady()` siempre |

**Conclusión:** no es obligatoria para “Catálogo warehouse + ELT + parte de analytics”; sí lo es para **subconjunto grande de reportes simples** y para módulos publishing.

### 4.2 ¿Org demo auto-seleccionada sin CRUD?

**Sí, es la opción recomendada.**  
El contexto ya existe; el menú Organizations es lo prescindible. Seed debe garantizar membership del admin/engineer a una org demo.

### 4.3–4.7 Publishing / Rights / Profiles

- **No indispensables** para narrativa core.  
- **Conservar ocultos** como avanzados / roadmap.  
- Quitar solo menú: **no rompe** backend; deep-links siguen si no se gated. Para “posponer seguro” hace falta **pequeña modificación** futura: añadir prefijos a `OUT_OF_PRODUCT_PATH_PREFIXES` + `DEMO_SECTION_IDS` (o productSurface), **tras aprobación** — no ahora.  
- Catálogo mínimo = warehouse steward (§3 D2).

---

## 5. Clasificación revisada

| Módulo | Clasificación anterior | Propuesta nueva | Tu veredicto | Evidencia | Dependencias | Riesgo |
| ------ | ---------------------- | --------------- | ------------ | --------- | ------------ | ------ |
| Streaming listener (Discover, search, tracks, playlists, liked, player) | MANTENER | NÚCLEO VISIBLE | **NÚCLEO VISIBLE** | Rutas + engagement APIs COMPLETE | dim_*, app_favorite/playlist, audio | Bajo ocultar |
| Activity (= history+activity) | FUSIONAR | NÚCLEO VISIBLE | **NÚCLEO VISIBLE** (tras fusión) | `/history`, `/activity`, listening-history | `app_listening_history` | Bajo |
| Settings (+ perfil) | MANTENER / FUSIONAR users | NÚCLEO VISIBLE | **NÚCLEO VISIBLE** | `/settings`, `/users` | identity, security | Bajo |
| Smart rails / AI etiquetado | MANTENER CON AJUSTES | NÚCLEO/SECUNDARIO en Discover | **SECUNDARIO VISIBLE** (dentro Discover) | `/smart/*`, `/ai/*` mock | analytics features | Medio claim |
| Workpanel | MANTENER | NÚCLEO VISIBLE staff | **NÚCLEO VISIBLE** | `/workpanel`, staff guard | org opcional; seeds | Medio sin datos |
| Reportes (hub/simple/complex) | MANTENER | NÚCLEO VISIBLE staff | **NÚCLEO VISIBLE** | staff routes + APIs | **muchos simple org_scoped** | Medio sin org |
| Catálogo warehouse tracks/artists/genres | implícito en streaming | NÚCLEO VISIBLE admin | **NÚCLEO VISIBLE** (admin) | catalog routes; create track 403 | dim_*; ELT | Bajo |
| Data Ops (ELT+Explorer) | MANTENER separado | NÚCLEO VISIBLE engineer | **NÚCLEO VISIBLE** (nav unificada) | `/elt-pipeline`, `/explorer` | PB, parquet, DuckDB | Alto demo vacía |
| Organizations UI | MANTENER | POSPONER menú | **OCULTO PERO FUNCIONAL** | org routes + shell hydrate | members, reportes | **Alto** si se apaga contexto |
| Catalog Publishing | MANTENER CON AJUSTES | POSPONER | **OCULTO PERO FUNCIONAL** | `/catalog`, org guards | Organizations | Bajo menú / Medio guión 031 |
| Catalog Rights | MANTENER CON AJUSTES | POSPONER | **OCULTO PERO FUNCIONAL** | catalog-rights routes | Organizations | Idem |
| Artist Profiles (org) | MANTENER | POSPONER | **OCULTO PERO FUNCIONAL** | `/artist-profiles` | Organizations | Idem |
| CRM / Billing / Royalties / Campaigns / BA / CS / Compliance / Subs B2B | POSPONER | POSPONER | **POSPONER** (+ **NO ELIMINAR POR DEPENDENCIAS** datos) | OUT_OF_PRODUCT; seeds/reportes | simple_reports SQL | **Alto** borrar tablas |
| Personal Account billing/plans | POSPONER | POSPONER | **POSPONER** | `/account/*` mock | personal_* | Medio |
| Business Decisions | POSPONER | POSPONER | **POSPONER** | ya bloqueado | — | Bajo |
| Platform Ops | SIMPLIFICAR | POSPONER nav | **OCULTO PERO FUNCIONAL** | ya hidden primary | audio unresolved útil | Bajo |
| `/recommendations` page | SIMPLIFICAR | POSPONER/quitar | **POSPONER** (contenido → Discover) | ruta viva | smart | Bajo |
| `/audio-features` | POSPONER | POSPONER | **POSPONER** | ya hidden listener | — | Bajo |
| Analytics FE huérfanos | ELIMINAR | ELIMINAR | **ELIMINAR TRAS VALIDACIÓN** | redirects only | services analytics VIVOS | Bajo |
| `features/*`, SpotifyLink, ReportsTypeTabs, ReportsListPage | ELIMINAR | ELIMINAR | **ELIMINAR TRAS VALIDACIÓN** | 0 consumidores | — | Bajo |
| Guards unused exports | ELIMINAR | ELIMINAR | **ELIMINAR TRAS VALIDACIÓN** | no en routes | otros guards vivos | Bajo |
| BE `packages/users` | ELIMINAR | ELIMINAR | **ELIMINAR TRAS VALIDACIÓN** (CAUTION tests) | shim identity | test_packages_d2 | Medio |
| `/api/v2` | ELIMINAR fase 2 | no tocar | **NO ELIMINAR POR DEPENDENCIAS** (externos desconocidos) | 0 FE | adapters | Alto |
| Tablas enterprise / packages CRM… | POSPONER | no borrar | **NO ELIMINAR POR DEPENDENCIAS** | Workpanel/report queries | seeds | Alto |
| Audio streaming services | MANTENER | no tocar | **NÚCLEO** / no eliminar | player | YouTube/Audius | Crítico |
| Design system enterprise-* | MANTENER | base CRUD | **NÚCLEO infra UI** | shared/enterprise | — | — |

---

## 6. Menú mínimo viable por rol (recomendado)

### Usuario — **validado, sin entradas extra obligatorias**

- Discover  
- Buscar  
- Canciones  
- Playlists  
- Me gusta  
- Actividad  
- Configuración  
- (+ reproductor global, no es ítem de menú)

**No obligatorias:** Organizations, recomendaciones, audio-features, planes.

### Administrador

Propuesta del usuario: Workpanel · Catálogo · Reportes · Configuración.

| Entrada | ¿Obligatoria? | Nota |
|---------|---------------|------|
| Workpanel | Sí | Home semántico staff |
| Catálogo | Sí | Debe mapear a `/tracks` (+ artists/genres), **no** `/catalog` publishing |
| Reportes | Sí | Preferir hub `/reports` |
| Configuración | Sí | |
| Organizations | **No en menú** | Pero **org demo activa** recomendada |
| Data Ops / ELT | No en menú admin *mínimo* | Admin ya tiene `hasEngineerAccess`; opcional “avanzado” — no añadir solo por existir |
| Platform Ops | No | |

**Entrada adicional técnicamente recomendada (no “porque existe”):** ninguna de menú; sí **bootstrap org silencioso**.

### Ingeniero

- Data Ops (ELT + Explorer + estado/cargas/validaciones reales)  
- Workpanel  
- Reportes  
- Configuración  

**No obligatorias en menú:** Platform Ops, Organizations CRUD, Publishing.

**Validaciones “que realmente existan”:** loads (`/stats/loads`), warehouse status, explorer preview, errores de import — **no** inventar UI de calidad si no hay endpoint.

---

## 7. Dependencias que impiden ocultar (o apagar) módulos

| Dependencia | Impide ocultar menú? | Impide apagar código/datos? |
|-------------|----------------------|------------------------------|
| `OrganizationContextService` en shell | No | **Sí** apagar servicio |
| Simple reports `org_scoped` | No (si hay org auto) | Sí quitar tablas/membership |
| Workpanel métricas org | No | Preferible mantener |
| Queries reportes sobre CRM/billing/… | No (UI ya oculta) | **Sí** DROP tablas |
| Publishing guards | No | Rutas pueden quedar |
| Player / audio services | N/A | **Nunca** eliminar en limpieza |
| Analytics **services** FE | N/A | No borrar con componentes huérfanos |

---

## 8. Módulos que pueden ocultarse inmediatamente (solo menú / deep-link policy — tras aprobación)

| Módulo | Cómo (futuro, no ahora) | Riesgo |
|--------|-------------------------|--------|
| Organizations CRUD | Quitar de `adminNavGroupConfig` / `PRODUCT_FINAL` | Bajo si org auto |
| Publishing / Rights / Artist Profiles | Mover a DEMO / OUT_OF_PRODUCT | Bajo–medio |
| Ya ocultos 038 | Mantener | — |
| Recommendations, audio-features | Fuera menú + redirect opcional | Bajo |
| Platform Ops | Ya fuera primario | — |
| Personal plans/billing | Ya / POSPONER | Bajo |

**No “inmediatamente” sin plan:** apagar hidratación org; borrar packages; DROP SQL.

---

## 9. Primera limpieza segura (oleada 1 — candidatos)

| Elemento | Consumidores | Rutas | Tests | Docs | Consecuencia | Veredicto | Pruebas |
|----------|--------------|-------|-------|------|--------------|-----------|---------|
| Analytics FE Dashboard/Trending/Comparatives/Analytics | Solo `features/dashboard` re-export; redirects | Redirects OK | `phase-c-routes.spec` paths stale | Specs históricos | Quitar UI muerta; **conservar** `packages/analytics/services` | **SAFE** | Build FE; navegar `/analytics`→workpanel |
| `features/*` | 0 imports app | — | — | — | Nulo | **SAFE** | Build FE |
| SpotifyLinkComponent | 0 templates | — | — | — | Nulo | **SAFE** | Build FE |
| ReportsTypeTabsComponent | 0 | — | — | specs 043/044 mencionan | Nulo | **SAFE** | `/reports` hub |
| ReportsListPage | No en reporting.routes | Hub vivo | — | — | Nulo | **SAFE** | Hub reportes |
| `organizationPermissionGuard` export | No en routes | Otros org guards vivos | — | — | Quitar export muerto | **SAFE** | Org deep-link smoke (si se prueba) |
| `subscriptionsAuthGuard` | No usado | — | — | — | Quitar | **SAFE** | — |
| Import muerto `staffCapabilityGuard` en `app.routes.ts` | Guard **sí** usado en package routes | — | — | — | Solo quitar import | **SAFE** | Workpanel/reports abren |
| BE `packages/users` | Runtime 0; **test_packages_d2**; pyproject path | identity montado | test shim | TRACEABILITY | Actualizar test | **CAUTION** | `pytest` identity + test_packages_d2 |

**No autorizados en oleada 1:** `/api/v2`, tablas enterprise, CRM/Billing/…, audio services, streaming player, datos Workpanel/reportes, enterprise-* design kit, `stream-insights`/`top-tracks` (huérfanos relacionados — pueden ir en oleada 1.b tras grep).

---

## 10. Pruebas necesarias (cuando se apruebe implementar)

1. Build frontend.  
2. Login user → menú mínimo → Discover play → liked → playlist → activity → settings.  
3. Login admin → Workpanel sin 403 → Reportes (uno `org_scoped=False` y uno `True` con org auto) → Catálogo `/tracks` list/edit (no esperar create 200).  
4. Login engineer → ELT status → Explorer preview → Workpanel.  
5. Deep-link `/crm` → module-unavailable; `/catalog` (si se gated) comportamiento acordado.  
6. Pytest: auth, simple reports org header, workpanel, catalog steward, test_packages_d2 si se toca shim.  
7. Redirects legacy analytics intactos.

---

## 11. Decisiones que aún requieren aprobación humana

1. ¿Admin aterriza en `/workpanel` o se acepta `/discover` como default global?  
2. ¿Org demo **siempre** auto-seleccionada para staff, o solo cuando se abre un reporte org_scoped?  
3. ¿Deep-links de Publishing/Rights: solo fuera de menú, o también `productSurfaceGuard` / module-unavailable?  
4. ¿Catálogo admin incluye solo `/tracks` o también `/artists` + `/genres` como subítems? (recomendación: **los tres**)  
5. ¿Admin ve entrada Data Ops? (recomendación: **no** en menú mínimo; acceso por rol engineer tools si se desea después)  
6. ¿Fusionar Activity y Settings en la misma oleada que el menú, o menú primero con redirects?  
7. ¿Autorizar oleada 1 de borrado muerto tras esta respuesta?  
8. ¿Guión de defensa debe dejar de mencionar publishing 031 / orgs 016 como producto visible?

---

## 12. Contrapropuesta final de alcance

### Narrativa (aceptada)
VOXMETRIKS = plataforma musical + analítica empresarial + ingeniería de datos (ELT → warehouse), **sin** pretender SaaS comercial completo en la superficie visible.

### Superficie visible

| Rol | Menú |
|-----|------|
| Usuario | Discover · Buscar · Canciones · Playlists · Me gusta · Actividad · Configuración (+ player) |
| Admin | Workpanel · **Catálogo** (`/tracks`, `/artists`, `/genres`) · Reportes · Configuración |
| Engineer | **Data Ops** (ELT + Explorer + estado/cargas reales) · Workpanel · Reportes · Configuración |

### Oculto pero funcional (no borrar)
Organizations (contexto + seed), Publishing, Rights, Artist Profiles, Platform Ops, demos 038, personal billing, recommendations page, audio-features.

### Posponer / roadmap
Toda la capa comercial B2B y compliance como producto visible.

### Eliminar tras validación (oleada 1)
Solo código muerto listado en §9 (con CAUTION en shim users).

### No eliminar por dependencias
`/api/v2` (aún), tablas/packages enterprise, audio stack, analytics **services**, design kit.

### Condición de seguridad para ocultar Organizations
**Mantener** hidratación + membership demo; **quitar** CRUD del menú. Sin eso, demos de reportes org_scoped se degradan.

### Corrección vs auditoría v1
Publishing/Rights/Orgs UI dejan de ser “MVP admin visible”; pasan a avanzado/oculto. Catálogo warehouse pasa a ser el Catálogo admin real.

---

## 13. Relación con documentos previos

| Doc | Estado respecto a este debate |
|-----|-------------------------------|
| `voxmetriks-full-audit.md` | Parcialmente supersedido en clasificación admin MVP |
| `voxmetriks-role-audit.md` | Menús admin/engineer a actualizar tras aprobación |
| `voxmetriks-simplification-plan.md` | Oleada A = este debate; oleada B = §9 |
| `voxmetriks-deletion-candidates.md` | Confirmado SAFE/CAUTION |
| `voxmetriks-design-system-proposal.md` | Aceptado provisionalmente; sin implementar |
| `voxmetriks-audit-index.md` | Añadir enlace a este decision doc en próxima edición de índice (cuando se pida) |

---

**Fin del debate documentado. Sin modificaciones de código. Esperando aprobación humana.**
