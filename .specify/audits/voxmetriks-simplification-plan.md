# VOXMETRIKS — Plan de simplificación

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-simplification-plan.md` |
| **Fecha** | 2026-08-06 |
| **Estado** | Propuesta — **requiere aprobación** antes de modificar código |
| **Git** | Prohibido en esta fase |

---

## Leyenda

| Campo | Valores |
|-------|---------|
| **Clasificación** | MANTENER · MANTENER CON AJUSTES · SIMPLIFICAR · FUSIONAR · ELIMINAR · POSPONER |
| **Prioridad** | P0 crítica · P1 alta · P2 media · P3 baja |
| **Esfuerzo** | S &lt;1d · M 1–3d · L &gt;3d |
| **Riesgo** | Bajo · Medio · Alto |
| **Orden** | Secuencia sugerida de ejecución tras aprobaciones |

---

## Tabla maestra

| Orden | Elemento | Tipo | Ubicación | Clasificación | Acción recomendada | Dependencias | Riesgo | Prioridad | Esfuerzo | Validación necesaria |
|------:|----------|------|-----------|---------------|--------------------|--------------|--------|-----------|----------|----------------------|
| 1 | Narrativa producto MVP 038–044 | Decisión | `.specify` + docs | MANTENER | Congelar claim demo: música + Workpanel + ELT; B2B 015 = roadmap | Constitución vs PRODUCT_FEATURES | Bajo | P0 | S | Aprobación stakeholder |
| 2 | FE analytics huérfanos | Componentes | `packages/analytics/{dashboard,trending,comparatives,analytics}` | ELIMINAR | Borrar tras grep de imports; mantener redirects | Redirects `app.routes` / nav policy | Bajo | P1 | S | Build FE; rutas redirect intactas |
| 3 | FE `features/*` shims | Módulo | `src/app/features` | ELIMINAR | Eliminar re-exports | Ninguna ruta activa | Bajo | P1 | S | Compilación |
| 4 | SpotifyLinkComponent | Componente | shared | ELIMINAR | Eliminar si 0 consumidores | — | Bajo | P2 | S | Grep + build |
| 5 | ReportsTypeTabs / ReportsListPage | Componente/página | reporting | ELIMINAR | Eliminar no ruteados | Hub `/reports` | Bajo | P2 | S | Navegar hub reportes |
| 6 | Guards FE no usados | Código | org/subscriptions guards | ELIMINAR | Quitar exports muertos o cablear conscientemente | — | Bajo | P3 | S | Grep routes |
| 7 | BE `packages/users` shim | Paquete | `app/packages/users` | ELIMINAR | Eliminar tras confirmar solo re-export identity | Imports tests | Medio | P2 | S | Pytest identity/auth |
| 8 | History + Activity | Rutas/UX | `/history`, `/activity` | FUSIONAR | Una ruta “Actividad”; redirect de la otra | listening-history API | Medio | P1 | M | E2E listener activity |
| 9 | Users → Settings | Rutas/UX | `/users`, `/settings` | FUSIONAR | Perfil dentro de Settings; redirect `/users` | UserService, security API | Medio | P1 | M | Settings + prefs |
| 10 | Reports hub UX | Rutas | `/reports`, simple, complex | FUSIONAR | Menú único `/reports`; deep-links legacy | staffCapability | Medio | P1 | M | Abrir simple+complex |
| 11 | Catalog admin hubs | Paquetes | publishing + rights + artists | SIMPLIFICAR | Un hub con secciones; menos ítems menú | org perms | Medio | P2 | L | Flujo publish/review |
| 12 | Listener nav | Nav policy | `nav-access.policy` + layout | SIMPLIFICAR | Menú § role-audit usuario | Spec 043 | Bajo | P1 | S | Login user menú |
| 13 | Admin nav | Nav | layout | SIMPLIFICAR | Workpanel + Reportes + Orgs + Catálogo + Settings | Spec 043 | Bajo | P1 | S | Login admin menú |
| 14 | Engineer nav | Nav | layout | SIMPLIFICAR | ELT + Explorer + Workpanel + Reportes | engineerGuard | Bajo | P1 | S | Login engineer |
| 15 | ELT + Explorer | Páginas | data-engineering | FUSIONAR (opcional) | Shell “Data Ops” tabs | stats/import, explorer API | Medio | P2 | M | Import + preview |
| 16 | Enterprise empty/KPI dup | Shared UI | shared/components | FUSIONAR | Un MetricCard / EmptyState canónico | enterprise kit + musical | Medio | P2 | M | Visual CRUDs |
| 17 | Design system CRUD | Diseño | shared/enterprise | MANTENER CON AJUSTES | Adoptar kit existente; ver design proposal | Spec 043 | Medio | P2 | L | Checklist pantallas admin |
| 18 | Smart + AI etiquetado | Feature | smart, ai | MANTENER CON AJUSTES | Badges “reglas locales / mock” | ai/factory | Bajo | P2 | S | UI copy ES/EN |
| 19 | Personal-account billing | Módulo | personal-account | POSPONER | Fuera menú; rutas gated o retiradas después | simulatePayment | Medio | P2 | M | No romper profile selector |
| 20 | CRM UI | Módulo | crm | POSPONER | Mantener gated 038; no borrar BE | Workpanel counts?, seeds | Alto | P3 | L | Queries reportes |
| 21 | Billing UI + webhook | Módulo | billing | POSPONER + seguridad | Gated; endurecer webhook en fase seguridad | academic_mock | Alto | P1* | M | *Seguridad antes demo pública |
| 22 | Royalties UI | Módulo | royalties | POSPONER | Gated; simulado | reportes | Alto | P3 | L | Mapear SQL reports |
| 23 | Subscriptions B2B | Módulo | subscriptions | POSPONER | Gated | org tiers | Alto | P3 | L | Onboarding org |
| 24 | Campaigns / BA / CS / Compliance | Módulos | varios | POSPONER | Gated; no menú | simple_reports seeds | Alto | P3 | L | Grep table usage |
| 25 | `/api/v2` | API | `app/api/router.py` | ELIMINAR (fase posterior) | Deprecar → quitar si 0 consumidores externos | enterprise adapters | Alto | P2 | M | OpenAPI + búsqueda repo |
| 26 | Dual music stacks BE | Servicios | packages vs app/services | SIMPLIFICAR | Documentar winners; reducir adapters | route_policy | Alto | P3 | L | Regression catalog |
| 27 | Audio-source público | Seguridad | catalog tracks | MANTENER CON AJUSTES | Requerir auth o token firmado | player | Medio | P1 | M | Playback E2E |
| 28 | Rate limit / CORS prod | Seguridad | core/security | MANTENER CON AJUSTES | Activar límites en demos expuestas | config | Medio | P2 | S | Smoke API |
| 29 | Docs database.md | Docs | docs/database | MANTENER CON AJUSTES | Regenerar inventario tablas | schemas | Bajo | P2 | M | Diff vs DuckDB |
| 30 | Specs index lag | Docs | automation/specs README | MANTENER CON AJUSTES | Actualizar a 044 | feature.json | Bajo | P3 | S | Lectura índice |
| 31 | Etiquetas datos | UX/API | Workpanel, ELT, reports | MANTENER CON AJUSTES | real/synthetic/simulated/mock | Spec 037 | Medio | P1 | M | Demo script |
| 32 | Parquet/DuckDB bootstrap | Ops | data/, pipeline | MANTENER | Checklist demo reproducible | PB creds | Alto | P0 | M | Pipeline en máquina limpia |
| 33 | Recommendations route | Ruta | `/recommendations` | SIMPLIFICAR | Contenido en Discover; redirect | smart API | Bajo | P2 | S | Discover rails |
| 34 | Audio-features route | Ruta | `/audio-features` | POSPONER | Quitar de producto listener | — | Bajo | P3 | S | Menú user |
| 35 | Platform-ops nav | Módulo | platform-ops | SIMPLIFICAR | Fuera nav primario (ya); acceso deep-link staff | platformAdmin | Bajo | P3 | S | — |
| 36 | Business-decisions | Ruta | reporting | POSPONER | Mantener bloqueado 038 | — | Bajo | P3 | S | Guard |
| 37 | POST create track 403 | API | catalog | MANTENER | Documentar “ELT-owned”; no fingir CRUD | steward UX | Bajo | P2 | S | Docs admin |
| 38 | Presentation modes | Nav | layout | MANTENER CON AJUSTES | Solo guión etiquetado | demos | Medio | P2 | S | Guión defensa |
| 39 | Código muerto BE streaming routes | Archivos | streaming/routes | ELIMINAR | Quitar re-exports no montados | audio services vivos | Medio | P3 | S | Import graph |
| 40 | NotImplementedPayload | Schema | models | ELIMINAR | Si sin refs | — | Bajo | P3 | S | Grep |

\*P1 en seguridad aunque el módulo esté POSPONER en producto.

---

## Oleadas de trabajo (post-aprobación)

### Oleada A — Decisiones (sin código)
1. Aprobar módulos MANTENER  
2. Aprobar ELIMINAR candidatos  
3. Aprobar POSPONER (gated)  

### Oleada B — Limpieza segura código muerto
Órdenes 2–7, 39–40  

### Oleada C — Rol usuario
Órdenes 8, 9, 12, 18, 33, 34  

### Oleada D — Rol administrador
Órdenes 10, 11, 13, 16, 17  

### Oleada E — Rol ingeniero
Órdenes 14, 15, 31, 32  

### Oleada F — Diseño CRUD
Orden 17 (+ migración gradual pantallas)  

### Oleada G — Seguridad
Órdenes 21 (webhook), 27, 28  

### Oleada H — Rendimiento
Home multi-fetch, explorer limits, ELT async (no en tabla exhaustiva — ver full-audit §15)  

### Oleada I — Deprecaciones mayores
Órdenes 20–25 (solo tras mapear SQL dependencias)  

---

## Dependencias críticas entre filas

```
(1 narrativo) → (12/13/14 nav) → demos
(2 analytics UI) independiente de (25 api v2)
(8 history) independiente de (10 reports)
(20–24 POSPONER) bloquea DROP tablas hasta mapear reportes
(32 bootstrap datos) bloquea demo estable engineer
(27 audio auth) puede romper player si mal hecho → prueba E2E obligatoria
```

---

## Criterio de “listo para eliminar”

Un elemento solo pasa a eliminación **aprobada** si:

1. Aparece en `voxmetriks-deletion-candidates.md` con confianza ≥ Alta, **o**  
2. Confianza Media + validación manual documentada, **y**  
3. No hay consumidores en FE/BE/tests/reportes SQL, **y**  
4. El usuario aprobó expresamente esa fila.

---

## No hacer en esta fase

- Git commit/branch/push  
- Borrar tablas DuckDB enterprise  
- Reactivar menús 038 “para probar” en producto-final  
- Reescribir arquitectura package-by-domain  
- Crear componentes design system nuevos sin reutilizar enterprise kit  

---

**Fin del plan de simplificación.**
