# VOXMETRIKS — Auditoría técnica y funcional completa

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-full-audit.md` |
| **Fecha** | 2026-08-06 |
| **Alcance** | Frontend Angular, Backend FastAPI, DuckDB/Parquet/PocketBase |
| **Fase** | Inventario + clasificación (sin modificar código funcional) |
| **Feature activa** | 044 — product consolidation and data clarity |
| **Metodología** | Spec-Driven Development · criterio Negocio → proceso → caso de uso → datos → backend → frontend |

> **Regla de evidencia:** nada se clasifica solo por nombre. Cada afirmación cita rutas, paquetes o flujos verificados.  
> **No inventado:** no se afirman IA avanzada, compliance legal, pasarelas reales ni streaming licenciado.

---

## 1. Resumen ejecutivo

VOXMETRIKS es un monorepo con **dos narrativas de producto coexistentes**:

1. **Constitución / Spec 015:** plataforma B2B SaaS de gestión e inteligencia musical (organizaciones, CRM, billing, campañas, ROI).
2. **Entrega 038–044 / PRODUCT_FEATURES:** MVP demostrable = **música + actividad personal** (listener) + **organizaciones + publishing/rights + Workpanel/reportes** (admin) + **ELT + Warehouse Explorer** (engineer). CRM, billing, regalías, campañas, etc. tienen backend y UI, pero están **fuera del menú producto** (`productSurfaceGuard` / `OUT_OF_PRODUCT_PATH_PREFIXES`).

El núcleo musical (auth → catálogo → reproducción → favoritos → playlists → historial) es **completo UI→API→DuckDB**. El núcleo operativo de demo (Workpanel, reportes, ELT, explorer) también es **completo**. Los módulos de dinero (billing, royalties, personal checkout) **persisten en DuckDB pero son explícitamente mock**. Hay **código muerto / huérfano**: componentes de analytics redirigidos, superficie `/api/v2` sin consumidores FE, shim `packages/users`, componentes UI sin rutas.

**Estado general:** sistema **rico, defendible como demo académica de música + analytics + ELT**, pero **sobrecargado** por dominios enterprise ocultos (~570 endpoints backend, ~27 paquetes FE). Antes de nuevas features, conviene consolidar el producto visible y aislar (no necesariamente borrar ya) lo demo/oculto.

### Veredicto en una frase

> **Producto demostrable sólido en el camino musical + Workpanel/ELT; complejidad enterprise retenida bajo la alfombra; limpieza segura posible si se respeta el orden de aprobación.**

---

## 2. Estado general del sistema

| Dimensión | Estado | Evidencia |
|-----------|--------|-----------|
| Arquitectura | Package-by-domain **parcialmente coherente** | FE `apps/frontend/src/app/packages/*`; BE `apps/backend/app/packages/*` + capa legacy `app/api` + `app/services` |
| Auth / roles | **Implementado** identity `user\|admin\|engineer` + org RBAC + platform RBAC | `identity`, `platform_rbac`, guards FE |
| Catálogo musical | **Implementado** (lecturas públicas; mutaciones admin; create track siempre 403) | `catalog/routes/tracks.py` |
| Reproducción | **Implementado** (YouTube → Audius → demo; audio-source público) | streaming audio resolver |
| Engagement | **Implementado** | favorites, playlists, listening-history |
| Smart / AI | **Parcial** (reglas locales + provider mock opcional) | `ai/factory.py`, `/smart/*` |
| Workpanel / reportes | **Implementado** (staff) | workpanel, simple/complex reports |
| ELT Medallion | **Implementado** (PB → parquet → DuckDB) | `elt_pipeline.py`, `POST /stats/import` |
| Enterprise CRM/Billing/… | **Implementado en código; oculto en producto** | Spec 038 |
| Datos en repo | Parquet/DuckDB **gitignored**; carpeta `data/` vacía en snapshot | `.gitkeep` only |
| Docs de datos | **Desactualizados** (`docs/database` ~48 tablas vs 100+ en código) | — |

### Tensiones estructurales

| Tensión | Impacto |
|---------|---------|
| Constitución B2B vs MVP musical 038 | Riesgo de demo confusa si se muestra lo oculto |
| Dual Spec 030 (Workpanel vs Royalties) | Ambigüedad de índices |
| `/api/v1` canónico vs `/api/v2` adapter | Superficie muerta para FE |
| `catalog/artists` vs org `/artists` | Homónimos; separados por path/header |
| Enterprise UI kit vs UI musical | Diseño inconsistente entre CRUDs |

---

## 3. Inventario de módulos

### 3.1 Frontend packages (`apps/frontend/src/app/packages/`)

| Módulo | Propósito actual | Roles | Clasificación | Valor (1–5) | Demo (1–5) | Integración FE↔BE (1–5) |
|--------|------------------|-------|---------------|-------------|------------|-------------------------|
| `streaming` | Discover, search, tracks, artists, genres, playlists, liked, activity, audio-features | user (+ admin steward) | **MANTENER** | 5 | 5 | 5 |
| `history` | Historial de escucha | user | **MANTENER** / posible FUSIONAR con activity | 4 | 4 | 5 |
| `recommendations` | Pantalla recomendaciones | user | **SIMPLIFICAR** / evaluar POSPONER menú | 3 | 3 | 4 |
| `smart` | Widgets home inteligente | user | **MANTENER CON AJUSTES** | 4 | 4 | 4 |
| `ai` | Diálogo playlist IA | user | **MANTENER CON AJUSTES** (mock/rules) | 3 | 4 | 4 |
| `users` | Perfil `/users` | todos | **MANTENER** / FUSIONAR con settings | 4 | 3 | 5 |
| `administration` | Settings | todos | **MANTENER** | 4 | 3 | 5 |
| `personal-account` | Planes/household/billing B2C | user | **POSPONER** menú; backend mock | 2 | 2 | 4 |
| `organizations` | Orgs, members, roles, audit | admin | **MANTENER** | 5 | 4 | 5 |
| `catalog-publishing` | Hub + artist portal + review | admin | **MANTENER CON AJUSTES** | 4 | 4 | 5 |
| `catalog-rights` | Assets, releases, contracts, conflicts | admin | **MANTENER CON AJUSTES** | 4 | 3 | 5 |
| `artists` | Artist profiles org | admin | **MANTENER** | 4 | 3 | 5 |
| `workpanel` | Panel operativo staff | admin/engineer | **MANTENER** | 5 | 5 | 5 |
| `simple-reports` | Reportes tácticos | staff | **MANTENER** / FUSIONAR UX con hub | 5 | 5 | 5 |
| `complex-reports` | Reportes warehouse | staff | **MANTENER** / FUSIONAR UX con hub | 5 | 5 | 5 |
| `reporting` | Hub `/reports` + decisions (gated) | staff | **MANTENER** hub; decisions **POSPONER** | 4 | 4 | 5 |
| `data-engineering` | ELT + Explorer | engineer | **MANTENER** | 5 | 5 | 5 |
| `analytics` | Dashboards legacy | — | **ELIMINAR** UI muerta / FUSIONAR restos | 1 | 1 | 2 |
| `crm` | CRM comercial | demo | **POSPONER** (oculto) | 2 | 1* | 5 |
| `billing` | Facturación mock | demo | **POSPONER** | 2 | 1* | 4 |
| `royalties` | Regalías simuladas | demo | **POSPONER** | 2 | 1* | 4 |
| `subscriptions` | Planes B2B | demo | **POSPONER** | 2 | 1* | 5 |
| `campaigns` | Campañas/ROI | demo | **POSPONER** | 2 | 1* | 4 |
| `business-analytics` | KPIs negocio | demo | **POSPONER** | 2 | 1* | 4 |
| `customer-success` | CS + support | demo | **POSPONER** | 2 | 1* | 4 |
| `compliance` | Privacy/DSR | demo | **POSPONER** | 1 | 1* | 4 |
| `platform-ops` | Ops plataforma | platform_admin | **SIMPLIFICAR** / oculto en nav primario | 3 | 2 | 4 |

\*Valor demo **producto final** bajo; alto solo en modo `presentationMode`.

### 3.2 Backend packages (`apps/backend/app/packages/`)

| Paquete | Clasificación | Notas |
|---------|---------------|-------|
| `identity` | **MANTENER** | Auth canónica |
| `catalog` | **MANTENER** | Tracks/artists/genres/playlists catalog |
| `engagement` | **MANTENER** | Favorites, playlists user, history, activity, dashboard home |
| `analytics` | **MANTENER CON AJUSTES** | Stats, warehouse, explorer, smart, pipeline |
| `ai` | **MANTENER CON AJUSTES** | Provider mock por defecto |
| `organizations` | **MANTENER** | |
| `catalog_publishing` / `catalog_rights` / `artists` | **MANTENER** | MVP admin |
| `workpanel` / `simple_reports` / `complex_reports` / `reporting` | **MANTENER** | |
| `platform_ops` / `platform_rbac` | **MANTENER CON AJUSTES** | rbac sin HTTP propio |
| `crm` / `contracts` / `subscriptions` / `billing` / `campaigns` / `business_analytics` / `customer_success` / `compliance` / `royalties` / `personal_subscriptions` | **POSPONER** producto; **no borrar backend aún** (seeds/reportes/Workpanel) | Spec 038 |
| `streaming` | **SIMPLIFICAR** | Compat re-export; servicios audio vivos |
| `users` | **ELIMINAR** candidato (shim de identity) | Sin imports runtime |

### 3.3 Capas legacy / paralelas

| Área | Ubicación | Clasificación |
|------|-----------|---------------|
| Enterprise v1 router | `app/api/enterprise_router.py` | **MANTENER CON AJUSTES** (solapa con packages) |
| API v2 | `app/api/router.py` `/api/v2` | **ELIMINAR** o marcar adapter-only (0 consumidores FE) |
| `app/services` + `repositories` | v2/enterprise | **SIMPLIFICAR** / FUSIONAR a packages |
| FE `features/*` | re-exports | **ELIMINAR** |
| FE analytics components sin ruta | dashboard, trending, comparatives, analytics | **ELIMINAR** candidatos |

---

## 4. Inventario de rutas (frontend)

### 4.1 Producto visible (shell autenticado)

| Ruta | Módulo | Guard | Clasificación |
|------|--------|-------|---------------|
| `/login` | pages | guestGuard | MANTENER |
| `/discover` | streaming/home | auth | MANTENER |
| `/search` | streaming | auth | MANTENER |
| `/tracks`, `/tracks/:id` | streaming | auth | MANTENER |
| `/artists`, `/artists/:id` | streaming | auth (oculto listener menú) | SIMPLIFICAR menú |
| `/genres` | streaming | auth (oculto listener) | SIMPLIFICAR |
| `/playlists`, `/playlists/:id`, `/playlists/catalog/:id` | streaming | auth | MANTENER |
| `/liked` | streaming | auth | MANTENER |
| `/history` | history | auth | MANTENER |
| `/activity` | streaming | auth | MANTENER / FUSIONAR con history |
| `/audio-features` | streaming | auth (oculto listener) | POSPONER o SIMPLIFICAR |
| `/recommendations` | recommendations | auth | SIMPLIFICAR |
| `/users` | users | auth | FUSIONAR → settings |
| `/settings` | administration | auth | MANTENER |
| `/account/profiles` | personal-account | auth | MANTENER CON AJUSTES |
| `/account/plans\|subscription\|household\|billing` | personal-account | auth | POSPONER |
| `/organizations/*` | organizations | org guards | MANTENER |
| `/catalog`, artist portal, review | catalog-publishing | org | MANTENER |
| `/catalog-rights/*` | catalog-rights | org | MANTENER |
| `/artist-profiles/*` | artists | org | MANTENER |
| `/workpanel` | workpanel | staffCapability | MANTENER |
| `/reports`, `/simple-reports`, `/complex-reports` | reporting hubs | staff | MANTENER / SIMPLIFICAR |
| `/elt-pipeline`, `/explorer` | data-engineering | engineerGuard | MANTENER |
| `/platform-ops/*` | platform-ops | platformAdmin | SIMPLIFICAR (fuera nav primario) |

### 4.2 Redirects canónicos (código vivo, pantallas destino muertas)

| From | To | Efecto |
|------|-----|--------|
| `/dashboard`, `/analytics`, `/insights/analytics`, `/dashboard/analytics` | `/workpanel` | Componentes analytics huérfanos |
| `/trending`, `/comparatives`, `/insights/tracks` | complex-reports / reports | Idem |
| `/etl-pipeline` | `/elt-pipeline` | Alias OK |

### 4.3 Fuera de producto (038) — deep-link → module-unavailable

`/crm/*`, `/billing/*`, `/royalties/*`, `/campaigns/*`, `/business-analytics/*`, `/customer-success/*`, `/support/*`, `/subscriptions/*`, `/compliance/*`, `/business-decisions/*`

**Clasificación:** **POSPONER** (no eliminar backend en fase 1).

---

## 5. Inventario de endpoints (backend)

### 5.1 Magnitud

| Métrica | Valor |
|---------|-------|
| Rutas HTTP registradas (`create_app()`) | **~570** |
| Públicas | ~50 |
| Auth `require_user_id` | ~120 |
| RBAC permission | ~364 |
| Staff / engineer / admin | ~29 |
| Superficies | `/api/v1` (canónica) + `/api/v2` (sin FE) |

### 5.2 Dominios por volumen (aprox.)

crm 53 · billing 39 · campaigns 30 · catalog-rights 29 · platform-ops 28 · compliance 26 · personal 22 · artists/reports/subscriptions ~19 · organizations 18 · tracks 16 · …

### 5.3 Endpoints críticos del MVP

| Método | Path | Auth | Consumidor FE | Estado |
|--------|------|------|---------------|--------|
| POST | `/users/login` … | PUBLIC | AuthService | COMPLETE |
| GET | `/tracks`, `/search`, `/music-search` | PUBLIC/auth | streaming | COMPLETE |
| GET | `/tracks/{id}/audio-source` | **PUBLIC** | player | COMPLETE (riesgo) |
| CRUD | `/favorites`, `/playlists` | auth | streaming | COMPLETE |
| * | `/listening-history`, `/me/listening-activity` | auth | history/activity | COMPLETE |
| GET | `/dashboard/home`, `/smart/*` | auth/optional | home | COMPLETE/PARTIAL |
| * | `/ai/*` | auth | ai dialog | PARTIAL (mock) |
| * | `/organizations/*` | RBAC | orgs | COMPLETE |
| * | publishing/rights/artists | RBAC | admin catalog | COMPLETE |
| GET | `/workpanel` | staff | workpanel | COMPLETE |
| * | `/reports/simple|complex/*` | staff | reports | COMPLETE |
| POST | `/stats/import`, `/stats/synthetic` | engineer | ELT UI | COMPLETE |
| GET | `/analytics/explorer/*` | engineer | explorer | COMPLETE |

### 5.4 Endpoints sin consumidor FE / redundantes

| Ítem | Evidencia | Clasificación |
|------|-----------|---------------|
| Todo `/api/v2/*` | FE `environment.apiUrl` = `/api/v1` únicamente | ELIMINAR / POSPONER adapter |
| `GET /api/v2/*/status` stubs | `module_status()` hardcode | ELIMINAR |
| `GET /tracks/top` vs `/stats/top-tracks` | solape semántico | SIMPLIFICAR |
| `GET /dashboard/overview` vs `/dashboard/home` | enterprise vs engagement | DOCUMENTAR / unificar |
| Alias `stats/energia` | legacy | SIMPLIFICAR |
| CRM/billing/… APIs | FE existe pero gated 038 | POSPONER (no borrar aún) |

### 5.5 Seguridad — hallazgos

| Hallazgo | Severidad | Notas |
|----------|-----------|-------|
| `GET …/audio-source` público | Media | Cualquiera con ID de track puede resolver fuente |
| `POST /billing/provider-events` sin bearer | Alta en prod | Firma opcional; secret academic default |
| Lecturas catálogo públicas | Baja (intencional) | OK para demo; documentar |
| Guards FE ≠ autoridad | Info | Backend es autoridad; correcto si RBAC BE está bien |
| CORS `*` solo no-prod | OK | Producción niega `*` |
| Rate limit global default 0 | Media | Desactivado por defecto |
| Create track siempre 403 | OK | Catálogo ELT-owned |

---

## 6. Inventario de datos

### 6.1 Flujo Medallion

```
PocketBase `datasets` (CSV)
  → data/bronze/raw_spotify.parquet
  → data/silver/silver_spotify.parquet
  → data/warehouse/voxmetrik.duckdb
       ├ dim_*, fact_*, agg_*, ctl_*     (analytics)
       └ app_*, personal_*, household_*  (runtime API)
  → FastAPI → Angular
```

**PocketBase:** única colección `datasets` (no es DB de usuarios).  
**Estado repo:** sin parquet/duckdb versionados (gitignore).

### 6.2 Tablas warehouse (analytics)

| Familia | Ejemplos | Uso |
|---------|----------|-----|
| Staging | `raw_spotify`, `bronze_*`, `silver_*` | ELT |
| Dims | `dim_track`, `dim_artista`, `dim_genero`, `dim_usuario`, … | Catálogo, search, reports |
| Facts | `fact_streaming`, `fact_favorites`, … | Analytics, smart, Workpanel |
| Aggs | `agg_top_*`, `agg_daily_streams`, … | Dashboards/reportes |
| Control | `ctl_carga_dataset`, `ctl_pipeline_stages`, … | ELT UI |

### 6.3 Tablas aplicación (MVP)

| Tabla | Uso |
|-------|-----|
| `app_user`, `app_session`, `app_email_code` | Auth |
| `app_favorite`, `app_playlist`, `app_playlist_track` | Biblioteca |
| `app_listening_history` | Actividad 035 |
| `app_track_audio_source`, covers | Playback |
| `app_organization*` | Orgs |
| `app_release_*`, `app_catalog_*`, `app_artist_profile*` | Publishing/rights/artists |

### 6.4 Tablas enterprise / personal (retenidas)

`app_crm_*`, `app_invoice*`, `app_campaign*`, `app_royalty_*`, `personal_*`, compliance, CS, etc. — **consumidas por seeds, simple_reports y Workpanel**; UI producto oculto.

### 6.5 Problemas de datos

| Problema | Clasificación |
|----------|---------------|
| Docs `database.md` desactualizado | MANTENER CON AJUSTES (docs) |
| Facts/aggs enterprise sintéticos | Debe etiquetarse (real/synthetic/simulated) |
| Sin VIEWs DuckDB | OK / documentar |
| Gold parquet opcional en disco | Gold vive en DuckDB |
| Campos no usados en UI | Auditar por tabla al limpiar reportes |

---

## 7. Evaluación detallada por módulo núcleo

Escala 1–5: Valor | Frecuencia | Complejidad | Mantenibilidad | Estabilidad | Calidad visual | Integración | Importancia demo.

### 7.1 Streaming (listener)

| Campo | Detalle |
|-------|---------|
| Propósito | Explorar y reproducir catálogo; biblioteca personal |
| Roles | `user` (principal), `admin` steward |
| Rutas | `/discover`, `/search`, `/tracks*`, `/playlists*`, `/liked`, `/activity`, … |
| Servicios | tracks, artists, genres, playlists, favorites, dashboard home |
| Endpoints | `/tracks*`, `/catalog/artists`, `/genres`, `/playlists`, `/favorites`, `/dashboard/home` |
| Datos | `dim_*`, `app_favorite`, `app_playlist*`, audio sources |
| Flujo | COMPLETE |
| Problemas | audio-features técnico en superficie; artistas/géneros CRUD mezclados con browse; covers inconsistentes |
| Dependencias | playback-core, shared music UI, identity |
| Riesgo eliminar | **Crítico** — no eliminar |
| Scores | 5/5/4/3/4/4/5/5 |
| Clasificación | **MANTENER** (+ SIMPLIFICAR navegación listener) |

### 7.2 History + Activity

| Campo | Detalle |
|-------|---------|
| Propósito | Historial y actividad personal (035) |
| Flujo | COMPLETE → `app_listening_history` |
| Problemas | Dos entradas de menú (`/history`, `/activity`) con solape |
| Clasificación | **FUSIONAR** en una superficie “Tu actividad” |
| Scores | 4/4/2/4/5/3/5/4 |

### 7.3 Organizations

| Campo | Detalle |
|-------|---------|
| Propósito | Multi-org, members, roles, audit |
| Flujo | COMPLETE |
| Problemas | Complejidad de tiers/onboarding para demo corta |
| Clasificación | **MANTENER** / **SIMPLIFICAR** onboarding para demo |
| Scores | 5/3/4/3/4/3/5/4 |

### 7.4 Catalog publishing + rights + artist profiles

| Campo | Detalle |
|-------|---------|
| Propósito | Ciclo de publicación y derechos MVP admin |
| Flujo | COMPLETE (permisos org) |
| Problemas | Muchas pantallas; tres paquetes; menús densos |
| Clasificación | **MANTENER CON AJUSTES** · **SIMPLIFICAR** a hub único |
| Scores | 4/3/5/3/4/3/5/4 |

### 7.5 Workpanel + Reports

| Campo | Detalle |
|-------|---------|
| Propósito | Control táctico + 33 reportes simples + complejos |
| Flujo | COMPLETE |
| Problemas | Tres rutas (`/reports`, `/simple-reports`, `/complex-reports`); reporting executive gated |
| Clasificación | **MANTENER** · **FUSIONAR** UX bajo hub `/reports` |
| Scores | 5/4/4/3/4/3/5/5 |

### 7.6 Data engineering (ELT + Explorer)

| Campo | Detalle |
|-------|---------|
| Propósito | Demostrar Medallion PB→Parquet→DuckDB |
| Flujo | COMPLETE (animación UI parcialmente teatral) |
| Problemas | Dos pantallas; depende de credenciales PB y datos locales |
| Clasificación | **MANTENER** · opcional **FUSIONAR** tabs en un “Data Ops” |
| Scores | 5/2/4/3/4/3/5/5 |

### 7.7 Analytics package (FE)

| Campo | Detalle |
|-------|---------|
| Propósito histórico | Dashboards/trending/comparatives |
| Estado flujo | **DEAD** — rutas redirigen a workpanel/reports |
| Clasificación | **ELIMINAR** componentes no referenciados (tras validar imports) |
| Scores | 1/1/3/2/2/2/2/1 |

### 7.8 Enterprise demos (CRM, Billing, …)

| Campo | Detalle |
|-------|---------|
| Estado | Backend + UI completos; producto-final los oculta |
| Valor producto actual | Bajo para demo musical |
| Riesgo eliminar | **Alto** — Workpanel/reportes/seeds dependen de tablas |
| Clasificación | **POSPONER** eliminación; mantener gated |
| Scores | 2/1/5/2/3/3/5/2 |

---

## 8. Problemas críticos

1. **Identidad de producto ambigua** (B2B constitución vs MVP 038) — confunde demo y roadmap.
2. **Superficie API enorme (~570)** con mayoría enterprise — coste de mantenimiento y ataque.
3. **Webhook billing público** con secret academic — inseguro si se despliega.
4. **Audio-source público** — exposición de resolución de fuentes.
5. **Código UI muerto** (analytics redirigidos) — ruido y riesgo de “revivir” pantallas rotas.
6. **Datos warehouse ausentes en repo** — demo falla sin pipeline/PB local.
7. **Mock money sin etiqueta uniforme** en toda la UI — riesgo académico de sobreclaim.

---

## 9. Problemas importantes

1. Duplicación empty-state / KPI cards / page headers (enterprise vs musical).
2. `/users` vs `/settings` vs personal-account.
3. History vs activity.
4. Dual `/artists` (catálogo musical vs org profiles).
5. Specs index desfasado (README 042 vs feature 044).
6. `docs/database` incompleto.
7. AI/smart presentados como “IA” sin aclarar reglas locales/mock.
8. ELT UI con timeline cosmético puede interpretarse como orquestación real más rica de lo que es.
9. Guards definidos pero no usados (`organizationPermissionGuard`, `subscriptionsAuthGuard`).
10. Rate limiting desactivado por defecto.

---

## 10. Código muerto o sin uso

| Elemento | Evidencia | Confianza |
|----------|-----------|-----------|
| FE `analytics/dashboard`, `trending`, `comparatives`, `analytics/analytics` | Rutas redirect; sin loadComponent | Alta |
| FE `features/*` re-exports | No usados por app.routes | Alta |
| FE `SpotifyLinkComponent` | Solo auto-ref | Alta |
| FE `ReportsTypeTabsComponent` | Solo auto-ref | Alta |
| FE `ReportsListPage` | Fuera de reporting.routes | Alta |
| BE `/api/v2` | 0 hits FE | Alta |
| BE `packages/users` | Shim identity; sin include propio | Alta |
| BE `streaming/routes` re-exports | No montados en main | Media-Alta |
| BE `NotImplementedPayload` | Schema sin uso | Media |
| Guards FE unused | `organizationPermissionGuard`, `subscriptionsAuthGuard` | Alta |

---

## 11. Duplicaciones

| Par | Acción recomendada |
|-----|-------------------|
| EmptyState vs EnterpriseEmptyState | Unificar en design system |
| KpiCard vs EnterpriseStatCard | Unificar MetricCard |
| simple vs complex vs reporting hub | Unificar navegación |
| dashboard home vs workpanel vs business-analytics | Ya parcialmente resuelto por redirects |
| identity vs packages/users | Eliminar shim |
| catalog artists vs org artists | Mantener separados; renombrar UX |
| v1 enterprise routes vs package routes | Documentar COLLISION_WINNERS; reducir adapters |

---

## 12. Funciones incompletas / simuladas

| Función | Naturaleza |
|---------|------------|
| Billing payments | `academic_mock` / simulate |
| Royalties payouts | `SimulatedPayoutProvider` |
| Personal checkout | `simulatePayment` |
| AI provider | `mock` / reglas locales |
| Business analytics trends/comparatives | stubs de mensaje |
| POST create track | siempre 403 (intencional) |
| ELT timeline UI | cosmético sobre import real |
| Compliance “legal” | no afirmar cumplimiento normativo |

---

## 13. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Borrar tablas enterprise rompe reportes/Workpanel | Alto | Inventario de queries antes de DROP |
| Borrar UI demo sin gate rompe presentationMode | Medio | Mantener feature flag |
| Limpiar `/api/v2` rompe clientes externos desconocidos | Medio | Buscar consumidores fuera del monorepo; deprecar primero |
| Unificar history/activity pierde URL bookmark | Bajo | Redirect |
| Exponer módulos 038 en demo | Alto reputacional | Mantener productSurfaceGuard |
| DuckDB vacío en máquina limpia | Alto demo | Checklist de boot + pipeline |

---

## 14. Clasificación consolidada (módulos)

| Clasificación | Módulos |
|---------------|---------|
| **MANTENER** | streaming (core), identity/auth, engagement, organizations, workpanel, simple-reports, complex-reports, data-engineering, administration/settings, playback-core, shared music UI |
| **MANTENER CON AJUSTES** | smart, ai, catalog-publishing, catalog-rights, artists (org), reporting hub, analytics BE, platform-ops, platform_rbac |
| **SIMPLIFICAR** | nav listener, catalog admin hubs, settings tabs, platform-ops nav, reports paths |
| **FUSIONAR** | history+activity; users→settings; simple/complex bajo `/reports`; opcional ELT+explorer; enterprise UI primitives |
| **ELIMINAR** (candidatos) | FE analytics huérfanos; features shims; SpotifyLink; ReportsTypeTabs; ReportsListPage; BE users shim; (después) `/api/v2` si se confirma |
| **POSPONER** | crm, billing, royalties, subscriptions B2B, campaigns, business-analytics, customer-success, compliance, personal-account billing/plans, business-decisions, recommendations página dedicada |

---

## 15. Rendimiento (hallazgos)

| Hallazgo | Área |
|----------|------|
| Home smart puede disparar múltiples endpoints (`/smart/home`, dashboard, covers) | Listener |
| Explorer preview sin límites agresivos puede ser costoso | Engineer |
| Reportes complejos sobre fact_* sin paginación cuidadosa | Staff |
| ELT import bloqueante en request HTTP | Engineer |
| Bundles: muchos lazy routes (bien) pero paquetes demo siguen en árbol | Build |
| LIKE sobre dim_track en search | Catálogo |
| Polling platform notifications | Shell |

---

## 16. Componentes shared existentes vs propuestos

Ya existen (reutilizar/mejorar, **no recrear desde cero**):

| Existente | Equivalente propuesto |
|-----------|----------------------|
| `enterprise-page-header` | PageHeader |
| `enterprise-action-bar` | CrudToolbar |
| `enterprise-data-table` | DataTable |
| `enterprise-status-badge` | StatusBadge |
| `enterprise-empty-state` | EmptyState |
| `enterprise-loading-skeleton` | LoadingState |
| `enterprise-error-state` | ErrorState |
| `enterprise-form-field` | Form fields |
| `enterprise-stat-card` / `metric-card` / `kpi-card` | MetricCard (fusionar) |
| `confirm-dialog` | ConfirmDialog |
| Guards + `nav-access.policy` | PermissionGuard (policy ya centralizada) |

Faltan o están dispersos: FilterPanel unificado, DetailPanel estándar, Pagination única, FormDialog/FormPage patrón, RowActions menú consistente, SearchInput compartido.

Detalle: `.specify/design/voxmetriks-design-system-proposal.md`.

---

## 17. Recomendaciones (sin implementar aún)

1. **Congelar** narrativa de demo en MVP 038–044 (música + Workpanel + ELT); tratar B2B 015 como roadmap, no como claim de entrega.
2. **Aprobar lista MANTENER / ELIMINAR / POSPONER** antes de tocar código.
3. Limpieza segura: UI muerta FE → shims → documentar deprecación `/api/v2`.
4. Unificar CRUD admin sobre enterprise kit existente.
5. Fusionar history/activity y users/settings.
6. Etiquetar siempre datos `real | synthetic | simulated | mock`.
7. Checklist demo: pipeline + PB + usuarios seed + roles.
8. Seguridad: auth en audio-source (o token corto); endurecer webhook billing; rate limit en demos públicas.
9. No eliminar tablas enterprise hasta mapear dependencias de reportes.
10. Continuar en orden de secciones 14 del brief del usuario.

---

## 18. Archivos relacionados de esta auditoría

| Archivo | Contenido |
|---------|-----------|
| `.specify/audits/voxmetriks-role-audit.md` | Auditoría por rol |
| `.specify/audits/voxmetriks-simplification-plan.md` | Plan tabular de acciones |
| `.specify/audits/voxmetriks-deletion-candidates.md` | Solo candidatos a borrado |
| `.specify/design/voxmetriks-design-system-proposal.md` | Sistema visual CRUD |

---

## 19. Fuentes de evidencia (principales)

- `apps/frontend/src/app/app.routes.ts`
- `apps/frontend/src/app/core/navigation/nav-access.policy.ts`
- `apps/frontend/src/app/packages/README.md`
- `apps/frontend/src/app/layouts/dashboard-layout/`
- `apps/backend/app/main.py` (+ route dump create_app)
- `apps/backend/app/api/route_policy.py`
- `docs/PRODUCT_FEATURES.md`
- `.specify/memory/constitution.md`
- `.specify/feature.json` (044)
- Specs 033–044, 038 hide demos, 030 workpanel
- `data/README.md`, `infrastructure/pocketbase/pb_migrations/`

---

**Fin del documento de auditoría completa.**  
**Siguiente paso:** aprobación humana de clasificaciones; **no modificar código funcional** hasta entonces.
