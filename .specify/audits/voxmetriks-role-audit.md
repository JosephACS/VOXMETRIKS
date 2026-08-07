# VOXMETRIKS — Auditoría por roles

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-role-audit.md` |
| **Fecha** | 2026-08-06 |
| **Roles identity** | `user` · `admin` · `engineer` |
| **Roles adicionales** | Org permissions · CRM platform_admin · presentation/artist/finance demos |
| **Política** | `nav-access.policy.ts` + Specs 034 / 038 / 043 |

---

## 0. Principio

Una pantalla solo se recomienda para un rol si:

1. Tiene propósito empresarial claro para ese rol.
2. Tiene flujo verificable UI → API → datos.
3. No es solo decorativa ni mock sin etiqueta.
4. No duplica otra superficie ya canónica.

---

## 1. Auditoría del rol Usuario (`user` / listener)

### 1.1 Objetivo del rol

Explorar el catálogo musical, reproducir (demo), gestionar biblioteca personal (favoritos, playlists), ver actividad propia, y ajustar preferencias de cuenta — **sin** operar warehouse, reportes staff ni módulos enterprise ocultos.

### 1.2 Qué necesita realmente

| Necesidad | Existe hoy | Estado flujo | Recomendación |
|-----------|------------|--------------|---------------|
| Inicio / Discover | `/discover` | COMPLETE | MANTENER |
| Buscar | `/search` | COMPLETE | MANTENER |
| Ver tracks / detalle | `/tracks`, `/tracks/:id` | COMPLETE | MANTENER |
| Reproducir | player-bar + audio-source | COMPLETE | MANTENER |
| Favoritos | `/liked` | COMPLETE | MANTENER |
| Playlists | `/playlists*` | COMPLETE | MANTENER |
| Historial / actividad | `/history`, `/activity` | COMPLETE | **FUSIONAR** |
| Artistas browse | `/artists` (oculto en menú listener) | COMPLETE | Acceso vía search/detail; no menú |
| Géneros | `/genres` (oculto menú) | COMPLETE | Opcional vía discover |
| Audio features | `/audio-features` (oculto) | PARTIAL/técnico | **POSPONER** / quitar de rutas listener |
| Recomendaciones página | `/recommendations` | PARTIAL | Integrar en Discover; no menú separado |
| Smart home rails | widgets en home | PARTIAL/COMPLETE | MANTENER CON AJUSTES |
| AI playlist | diálogo | PARTIAL mock/rules | MANTENER CON AJUSTES + etiqueta |
| Perfil / prefs | `/users`, `/settings` | COMPLETE | **FUSIONAR** en Settings |
| Planes personales / billing | `/account/*` | mock pay | **POSPONER** |
| Profiles selector | `/account/profiles` | COMPLETE | MANTENER si household demo; si no, POSPONER |

### 1.3 Módulos necesarios

- `streaming` (núcleo)
- `history` (fusionar con activity)
- `playback-core` + shared player
- `administration` (settings)
- `smart` / `ai` (como ayudas de Discover, no como secciones enterprise)
- Auth (`identity` vía core)

### 1.4 Módulos innecesarios para el usuario

- Todo `DEMO_SECTION_IDS` / `OUT_OF_PRODUCT_PATH_PREFIXES`
- Workpanel, reports, ELT, explorer
- Catalog publishing/rights/artist-profiles (salvo membership org futura)
- Analytics legacy
- Platform-ops
- Compliance, CRM, billing B2B, royalties, campaigns, CS

### 1.5 Acciones principales

1. Login  
2. Discover → play  
3. Search → play / like / add to playlist  
4. Gestionar Liked + Playlists  
5. Ver actividad  
6. Ajustar settings / idioma  

### 1.6 Flujo de navegación recomendado

```
Login → Discover
          ├─ Search
          ├─ Library: Tracks | Playlists | Liked | Activity
          └─ Account: Settings
```

Player global persistente (ya existe).

### 1.7 Pantalla inicial

`/discover` (ya es redirect por defecto del shell).

### 1.8 Menú recomendado (listener)

| Sección | Ítems |
|---------|-------|
| Principal | Discover, Buscar |
| Biblioteca | Canciones, Playlists, Me gusta, Actividad |
| Cuenta | Configuración |

**Quitar del menú (si aún aparecen):** recomendaciones dedicadas, audio-features, artistas/géneros como CRUD, analytics, planes de pago (salvo demo explícita), organizations (salvo que el user tenga org — entonces sección org mínima).

### 1.9 Permisos necesarios

- Sesión Bearer (`require_user_id`) para mutaciones engagement.
- Lectura catálogo (hoy pública — aceptar para demo; endurecer post-demo si se exige).
- Sin staffCapability, sin engineerGuard, sin CRM.

### 1.10 Endpoints necesarios

`/users/login|me|preferences`, `/tracks*`, `/playlists`, `/favorites`, `/listening-history`, `/me/listening-activity`, `/dashboard/home`, `/smart/*` (opcional), `/ai/*` (opcional), `/security/*` (settings).

### 1.11 Datos necesarios

`dim_track/artista/genero`, `app_user`, `app_favorite`, `app_playlist*`, `app_listening_history`, `app_track_audio_source`, covers.

### 1.12 Eliminar / fusionar (vista usuario)

| Acción | Elemento |
|--------|----------|
| Fusionar | `/history` + `/activity` |
| Fusionar | `/users` → `/settings` |
| Posponer | `/account/plans|billing|subscription|household` |
| Posponer menú | `/recommendations`, `/audio-features` |
| No mostrar | cualquier deep-link 038 |

### 1.13 Scores agregados (listener core)

| Criterio | Score |
|----------|-------|
| Valor empresarial (demo musical) | 5 |
| Claridad de flujo | 4 (baja por duplicados history/users) |
| Estabilidad demo | 4 |
| Complejidad innecesaria | Media-alta por restos de menú histórico |

---

## 2. Auditoría del rol Administrador (`admin`)

### 2.1 Objetivo del rol

Operar el producto musical empresarial **visible**: organizaciones, ciclo de catálogo (publishing/rights/artists), Workpanel y reportes; además capacidades de steward de catálogo y acceso engineer.

### 2.2 Qué necesita realmente

| Necesidad | Superficie actual | Estado | Recomendación |
|-----------|-------------------|--------|---------------|
| Workpanel | `/workpanel` | COMPLETE | MANTENER · home admin |
| Reportes simples/complejos | `/reports` hub + rutas | COMPLETE | MANTENER · SIMPLIFICAR a un hub |
| Organizaciones | `/organizations/*` | COMPLETE | MANTENER · SIMPLIFICAR onboarding demo |
| Catalog hub | `/catalog` | COMPLETE | MANTENER |
| Publishing / review | artist portal + catalog-review | COMPLETE | MANTENER CON AJUSTES |
| Rights | catalog-rights | COMPLETE | MANTENER CON AJUSTES |
| Artist profiles | `/artist-profiles` | COMPLETE | MANTENER |
| Settings | `/settings` | COMPLETE | MANTENER |
| Mutaciones catálogo warehouse | tracks/genres admin | COMPLETE (create track 403) | Documentar límites ELT |
| CRM / Billing / Royalties / Campaigns / CS / Compliance / B2B subs | rutas 038 | COMPLETE pero oculto | **POSPONER** — no en menú producto |
| Platform ops | `/platform-ops` | COMPLETE | SIMPLIFICAR; no nav primario |
| Analytics legacy dashboards | redirects | DEAD UI | ELIMINAR restos |

### 2.3 Módulos necesarios

- `workpanel`, `simple-reports`, `complex-reports`, `reporting` (hub)
- `organizations`
- `catalog-publishing`, `catalog-rights`, `artists`
- `administration`
- Acceso a herramientas engineer (`data-engineering`) según política actual admin=engineer access
- Streaming opcional (validar experiencia)

### 2.4 Módulos innecesarios en menú producto

Todos los `DEMO_SECTION_IDS` + business-decisions + personal billing + analytics section + recommendations como sección staff.

### 2.5 Acciones principales

1. Login como admin  
2. Workpanel — salud del sistema / métricas  
3. Reportes — abrir 1 simple + 1 complejo  
4. Organizaciones — ver/crear org, members  
5. Catálogo — hub → release/review o rights  
6. (Opcional) Settings  

### 2.6 Flujo de navegación recomendado

```
Login → Workpanel
          ├─ Reportes (hub: simples | complejos)
          ├─ Organizaciones → Hub org
          ├─ Catálogo → Publishing | Rights | Artistas
          └─ Configuración
```

### 2.7 Pantalla inicial

`/workpanel` (ya es el único ítem `STAFF_MAIN_PRODUCT_PATHS`).

### 2.8 Menú recomendado (admin)

| Sección | Ítems |
|---------|-------|
| Principal | Workpanel |
| Reportes | Reportes (hub) |
| Organizaciones | Organización activa / crear |
| Catálogo | Hub catálogo, Perfiles artista, Derechos (o todo bajo Hub) |
| Cuenta | Configuración |

**Opcional avanzado (no demo corta):** Platform ops.

### 2.9 Permisos necesarios

- Identity `admin`
- Org permissions: `organization.*`, `member.*`, `publishing.*`, `royalty` no necesario en MVP visible
- Catalog steward (admin) para mutaciones warehouse
- Staff reports access

### 2.10 Endpoints necesarios

`/workpanel`, `/reports/simple/*`, `/reports/complex/*`, `/organizations/*`, `/artist-portal/*`, `/releases/*`, `/catalog-review/*`, `/catalog-rights/*`, `/artists/*` (org), `/users/me`, mutaciones admin de `/tracks`/`/genres` según steward.

### 2.11 Datos necesarios

Tablas `app_organization*`, publishing/rights/artists, `dim_*`/`fact_*`/`agg_*` para reportes, seeds enterprise **solo si** Workpanel/reportes los cuentan (no exponer UI CRM).

### 2.12 Eliminar / fusionar (vista admin)

| Acción | Elemento |
|--------|----------|
| Fusionar UX | simple + complex bajo `/reports` |
| Simplificar | tres paquetes catálogo → un hub con tabs |
| No añadir al menú | CRM, billing, royalties, campaigns… |
| Eliminar UI muerta | analytics dashboards |
| Evitar | panel admin decorativo duplicado del Workpanel |

### 2.13 Riesgo de “admin panel decorativo”

Ya mitigado parcialmente: Workpanel es canónico. Riesgo residual si se reactivan business-analytics / executive reporting sin narrativa.

---

## 3. Auditoría del rol Ingeniero de datos (`engineer`)

### 3.1 Objetivo del rol

Demostrar el **proceso de datos**: fuentes → ELT Medallion → warehouse DuckDB → exploración y (vía staff) Workpanel/reportes analíticos.

### 3.2 Qué necesita realmente

| Necesidad | Superficie | Estado | Recomendación |
|-----------|------------|--------|---------------|
| Estado / disparo ELT | `/elt-pipeline` | COMPLETE (UI parcialmente teatral) | MANTENER |
| Import PocketBase | `POST /stats/import` | COMPLETE | MANTENER |
| Synthetic loads | `POST /stats/synthetic` | COMPLETE | MANTENER CON etiqueta |
| Explorer tablas/preview | `/explorer` | COMPLETE | MANTENER |
| Workpanel | `/workpanel` | COMPLETE | MANTENER (vista métricas) |
| Reportes complejos | `/complex-reports` / hub | COMPLETE | MANTENER |
| Historial cargas | `/stats/loads` | COMPLETE vía ELT UI | MANTENER |
| Warehouse status | `/analytics/warehouse` | COMPLETE | MANTENER |
| Platform ops / unresolved audio | `/platform-ops` | COMPLETE | SIMPLIFICAR; útil para audio demo |
| CRM/Billing UI | 038 | — | No necesario |
| Analytics FE legacy | redirects | DEAD | ELIMINAR |
| Separar Data Eng / Explorer / Analytics | 3 conceptos | — | Ver §3.8 |

### 3.3 Módulos necesarios

- `data-engineering` (ELT + Explorer)
- `workpanel` + `complex-reports` (+ hub)
- `analytics` **backend** (stats/warehouse/explorer/pipeline)
- Opcional: `platform-ops` (audio unresolved)

### 3.4 Módulos innecesarios

- Enterprise demos comerciales
- Listener-only niceties (no bloquean)
- FE analytics package huérfano
- Compliance UI

### 3.5 Acciones principales

1. Login engineer  
2. ELT — ver estado, ejecutar import (si PB disponible)  
3. Explorer — listar tablas, preview `dim_track` / `fact_streaming`  
4. Workpanel — validar métricas post-carga  
5. Abrir un reporte complejo  

### 3.6 Flujo de navegación recomendado

```
Login → ELT Pipeline
          ├─ Warehouse Explorer
          ├─ Workpanel
          └─ Reportes (complejos)
```

### 3.7 Pantalla inicial

`/elt-pipeline` (hoy en menú engineer main junto a workpanel).  
Alternativa demo: Workpanel si el pipeline ya corrió en boot.

### 3.8 ¿Separar Data Engineering, Warehouse Explorer y Analytics?

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| Mantener ELT y Explorer separados | Claridad pedagógica | Dos clics | **Aceptable** |
| Fusionar en “Data Ops” con tabs | Menos menú | Más componente | **Preferida a medio plazo** |
| Mantener Analytics FE separado | — | Ya está muerto vía redirects | **No** — no revivir |
| Analytics = Workpanel + complex reports | Ya es el camino 038 | — | **Sí — canónico** |

**Veredicto:** ELT + Explorer pueden permanecer como dos rutas o fusionarse en un shell; **Analytics de producto = Workpanel + Reportes**, no el package `analytics` FE legacy.

### 3.9 Menú recomendado (engineer)

| Sección | Ítems |
|---------|-------|
| Principal | ELT Pipeline, Workpanel |
| Datos | Warehouse Explorer |
| Reportes | Reportes (hub) |
| Cuenta | Configuración |

### 3.10 Permisos necesarios

- Identity `engineer` (o `admin` con `hasEngineerAccess`)
- Endpoints engineer: import, synthetic, explorer, warehouse
- Staff reports

### 3.11 Endpoints necesarios

`/stats/import`, `/stats/synthetic`, `/stats/loads`, `/stats/summary`, `/analytics/warehouse`, `/analytics/explorer/tables`, `/analytics/explorer/preview/{table}`, `/workpanel`, `/reports/complex/*`.

### 3.12 Datos necesarios

PocketBase `datasets`, parquet bronze/silver (runtime), DuckDB `dim_*`/`fact_*`/`agg_*`/`ctl_*`, más tablas app si Workpanel las agrega.

### 3.13 Eliminar / fusionar

| Acción | Elemento |
|--------|----------|
| No revivir | `/analytics`, `/trending`, `/comparatives` UI |
| Fusionar opcional | ELT + Explorer |
| Etiquetar | synthetic vs PocketBase real |
| Documentar | ausencia de parquet en git |

---

## 4. Matriz rol–permiso–módulo

| Módulo / ruta | user | admin | engineer | Notas |
|---------------|:----:|:-----:|:--------:|-------|
| Discover / Search / Library | ✅ | ✅ | ✅ | |
| Activity | ✅ | ✅ | ✅ | |
| Settings | ✅ | ✅ | ✅ | |
| Recommendations page | ⚠️ | ⚠️ | ⚠️ | Simplificar / fuera menú |
| Organizations | ⚪ | ✅ | ⚪ | Si membership, acceso limitado |
| Catalog publishing/rights/artists | ❌ | ✅ | ⚪ | Org perms |
| Workpanel | ❌ | ✅ | ✅ | staffCapability |
| Reports hub | ❌ | ✅ | ✅ | |
| ELT / Explorer | ❌ | ✅* | ✅ | engineerGuard (*admin via hasEngineerAccess) |
| Platform ops | ❌ | ⚠️ | ⚠️ | platform_admin / engineer |
| CRM/Billing/Royalties/… | ❌† | ❌† | ❌† | †oculto product-final; presentationMode bypass |
| `/api/v2` | — | — | — | sin FE |

Leyenda: ✅ menú/uso · ⚠️ existe pero no recomendado · ⚪ condicional · ❌ no producto.

---

## 5. Menús recomendados (resumen)

### Usuario
Discover · Buscar · Canciones · Playlists · Me gusta · Actividad · Configuración

### Administrador
Workpanel · Reportes · Organizaciones · Catálogo · Configuración

### Ingeniero
ELT Pipeline · Explorer · Workpanel · Reportes · Configuración

---

## 6. Flujos recomendados (resumen demo)

| Rol | Script corto |
|-----|--------------|
| Usuario | Login → Discover → play → like → playlist → activity |
| Admin | Login → Workpanel → reporte → org → catalog hub |
| Engineer | Login → ELT status/run → Explorer preview → Workpanel |

---

## 7. Elementos que sobran por rol

### Usuario
- Audio features, recomendaciones como sección, planes mock, deep-links enterprise, artists/genres CRUD, analytics.

### Administrador
- CRM/billing/royalties/campaigns/CS/compliance en menú, business-decisions, analytics legacy, duplicar “dashboards”, personal-account billing.

### Ingeniero
- Toda la superficie comercial 038, AI musical como foco, múltiples analytics FE, platform-ops denso en demo corta.

---

## 8. Presentation / demo modes (no son roles identity)

El layout soporta `presentationMode` / artist / finance demos que **bypass** filtros de producto.  
**Recomendación:** usarlos solo en guión académico etiquetado; el producto-final debe permanecer en la matriz de §4.

---

## 9. Decisiones pendientes de aprobación humana

1. ¿Fusionar Activity + History en una sola ruta?  
2. ¿Fusionar Users en Settings?  
3. ¿Fusionar ELT + Explorer en “Data Ops”?  
4. ¿Mantener personal-account plans en menú oculto o retirar rutas?  
5. ¿Admin home siempre Workpanel (sí recomendado)?  

---

**Fin auditoría por roles.**  
Ver también: `voxmetriks-full-audit.md`, `voxmetriks-simplification-plan.md`.
