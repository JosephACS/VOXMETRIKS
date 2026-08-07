# VOXMETRIKS — Checklist de revisión visual y UX

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-visual-review-checklist.md` |
| **Fecha** | 2026-08-06 |
| **Propósito** | Guía exacta de pantallas a abrir y capturar para auditoría visual externa |
| **Evidencia automática** | No generada — sin herramienta de captura de navegador en esta sesión |
| **Carpeta sugerida** | `.specify/audits/evidence/` (crear al tomar capturas reales) |

> **Importante:** las rutas son las **reales** del código (`app.routes.ts` + package routes). No existen `/home` ni `/admin/tracks`.  
> **No** uses capturas inventadas. Solo screenshots de la app en ejecución.  
> Anota cualquier diferencia entre lo documentado aquí y lo observado.

---

## 0. Cómo tomar las capturas

### 0.1 Preparación

1. Arrancar backend + frontend con datos seed / warehouse cargado (si warehouse vacío, documentarlo).
2. Usar tres cuentas: `user`, `admin`, `engineer` (o las del seed demo).
3. Idioma: capturar **ES** (default) y, al menos en 3 pantallas clave, **EN**.
4. Navegador Chromium; ventana desktop **1440×900** salvo donde se pida móvil/tablet.
5. Nombrar archivos: `NNN-rol-pantalla-estado.png` (ej. `001-user-discover-loaded.png`).
6. Guardar en `.specify/audits/evidence/` junto con un `NOTES.md` de errores encontrados.

### 0.2 Tipos de captura (marcar en cada fila)

| Código | Significado |
|--------|-------------|
| **FULL** | Pantalla completa (viewport + scroll si cabe en 1–2 shots) |
| **NAV** | Sidebar / menú visible y expandido |
| **FORM** | Formulario create/edit abierto |
| **MODAL** | Modal o confirm dialog abierto |
| **DATA** | Con registros reales |
| **EMPTY** | Sin datos / empty state |
| **VAL** | Validación de formulario visible |
| **ERR** | Mensaje de error |
| **LOAD** | Estado de carga (throttling red o refresh rápido) |
| **MOB** | Viewport móvil (~390×844) |
| **TAB** | Viewport tablet (~768×1024) |
| **PERM** | Acción permitida vs bloqueada según rol |

### 0.3 Cuentas y accesos esperados

| Rol identity | Home esperado | Menú esperado (producto-final) |
|--------------|---------------|--------------------------------|
| `user` | `/discover` | Discover, Search, library, Settings |
| `admin` | `/workpanel` (ítem principal staff) | Workpanel, Reportes, Orgs, Catálogo, Settings; + ELT/Explorer vía engineer access |
| `engineer` | `/elt-pipeline` o Workpanel | ELT, Explorer, Workpanel, Reportes |

---

## 1. Tabla maestra de capturas — Usuario

| N.º | Rol | Pantalla / módulo | Ruta | Acción o estado | Qué debemos revisar | Componentes visibles | Posibles problemas (código) | Tipo | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| U01 | Usuario | Login | `/login` | Formulario vacío | Branding, claridad, contraste | Auth layout, form | — | FULL | Alta |
| U02 | Usuario | Login error | `/login` | Credenciales inválidas | Mensaje de error claro ES | Alert/toast | Copy genérico | ERR | Alta |
| U03 | Usuario | Inicio Discover | `/discover` | Recién cargado con datos | Jerarquía, rails, CTAs, no “dashboard” genérico | Home, smart widgets, player bar | Multi-fetch home; smart parcial | FULL+NAV | Alta |
| U04 | Usuario | Discover carga | `/discover` | Throttle red / hard refresh | Skeletons vs spinners | Loading states | Inconsistencia loading | LOAD | Media |
| U05 | Usuario | Menú lateral | `/discover` | Sidebar expandido | Ítems listener; sin staff/enterprise | Sidebar sections | Ítems ocultos vía policy vs sorpresa deep-link | NAV | Alta |
| U06 | Usuario | Menú colapsado | `/discover` | Sidebar colapsado | Iconos + tooltips | Sidebar | Persistencia localStorage | NAV | Baja |
| U07 | Usuario | Catálogo canciones | `/tracks` | Listado con registros | Densidad, portadas, acciones play/like | Track list/table, filters | Mezcla browse + steward CRUD | FULL+DATA | Alta |
| U08 | Usuario | Catálogo vacío | `/tracks` | Filtro sin resultados o sin data | Empty state útil | EmptyState | Varios empty patterns | EMPTY | Media |
| U09 | Usuario | Detalle canción | `/tracks/:id` | Track existente | Jerarquía info, play, like, add playlist | Detail, actions | Covers inconsistentes | FULL | Alta |
| U10 | Usuario | Artistas listado | `/artists` | Abrir por URL (puede no estar en menú listener) | ¿Debe existir para user? Claridad | Artists list | **Oculto en menú** (`LISTENER_HIDDEN_MUSIC_PATHS`) | FULL+PERM | Alta |
| U11 | Usuario | Detalle artista | `/artists/:id` | Artista con tracks | Relación artista→tracks | Artist detail | — | FULL | Media |
| U12 | Usuario | Géneros | `/genres` | Abrir por URL | Utilidad para listener; CRUD visible? | Genres | **Oculto en menú**; steward UI | FULL+PERM | Alta |
| U13 | Usuario | Búsqueda | `/search` | Query con resultados | Relevancia UI, tipografía, play | Search results | Dual search endpoints | FULL+DATA | Alta |
| U14 | Usuario | Búsqueda vacía | `/search` | Query sin matches | Empty + sugerencias | Empty | — | EMPTY | Media |
| U15 | Usuario | Reproductor idle | `/discover` | Sin track | Player bar no invasivo | Player bar | — | FULL | Media |
| U16 | Usuario | Reproductor playing | `/tracks/:id` o Discover | Play track con fuente | Controles, seek, cover, errores fuente | Player, now-playing | Audio-source público; fallos YT | FULL | Alta |
| U17 | Usuario | Reproductor error | Cualquiera | Track sin fuente / failure | Mensaje honesto (no “streaming comercial”) | Error toast/inline | Fallbacks Audius/demo | ERR | Alta |
| U18 | Usuario | Playlists listado | `/playlists` | Con playlists | Cards vs lista; CTA crear | Playlists | — | FULL+DATA | Alta |
| U19 | Usuario | Playlist detalle | `/playlists/:id` | Abrir playlist | Reordenar/quitar si existe; play all | Playlist detail | — | FULL | Alta |
| U20 | Usuario | Crear playlist | `/playlists` | Abrir create (dialog/form) | Validación nombre; doble submit | Form/Modal | — | FORM+MODAL+VAL | Alta |
| U21 | Usuario | Favoritos | `/liked` | Con likes | Consistencia con heart en listas | Liked list | — | FULL+DATA | Alta |
| U22 | Usuario | Favoritos vacío | `/liked` | Sin likes (o user limpio) | Empty + CTA a Discover | EmptyState | — | EMPTY | Media |
| U23 | Usuario | Historial | `/history` | Con eventos | Claridad temporal | History | **Solapa con Activity** | FULL | Alta |
| U24 | Usuario | Actividad | `/activity` | Comparar con U23 | Duplicación percibida | Activity page | Fusión propuesta en auditoría | FULL | Alta |
| U25 | Usuario | Recomendaciones | `/recommendations` | Página cargada | Valor vs Discover; honestidad “IA” | Recommendations | Sección demo en policy; lógica parcial | FULL | Media |
| U26 | Usuario | Perfil | `/users` | Datos usuario | Campos útiles vs ruido | Users/profile | **Fusión → Settings** propuesta | FULL | Alta |
| U27 | Usuario | Configuración | `/settings` | Tabs disponibles | Prefs, idioma, seguridad; tabs engineer ocultos | Settings | Tabs técnicos solo engineer | FULL+PERM | Alta |
| U28 | Usuario | Settings idioma EN | `/settings` | Cambiar a EN + volver Discover | Strings rotas / keys crudas | i18n | enterprise vs core locales | FULL | Alta |
| U29 | Usuario | Profiles selector | `/account/profiles` | Si seed household | ¿Pertenece al MVP listener? | Profiles layout | Personal-account POSPONER | FULL | Baja |
| U30 | Usuario | Denied staff | `/workpanel` | Deep-link sin staff | 403 / redirect correcto | Error 403 | staffCapabilityGuard | ERR+PERM | Alta |
| U31 | Usuario | Module unavailable | `/crm` | Deep-link demo | Página module-unavailable | Error page | productSurfaceGuard 038 | ERR+PERM | Media |
| U32 | Usuario | Discover móvil | `/discover` | Viewport 390px | Player, nav drawer, jerarquía | Layout responsive | — | MOB | Alta |
| U33 | Usuario | Search tablet | `/search` | Viewport 768px | Resultados usables | Search | — | TAB | Media |
| U34 | Usuario | Tracks paginación | `/tracks` | Ir a página 2 si hay | Controles claros | Pagination | — | DATA | Media |

---

## 2. Tabla maestra — Administrador

> Nota: el admin **no** tiene un prefijo `/admin/*`. CRUD de catálogo warehouse vive en `/tracks`, `/artists`, `/genres` con rol steward. Gestión de “usuarios” de organización = `/organizations/:id/members` (no un admin users global separado en MVP).

| N.º | Rol | Pantalla / módulo | Ruta | Acción o estado | Qué debemos revisar | Componentes visibles | Posibles problemas (código) | Tipo | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | Admin | Login → home | `/login` → `/workpanel` o default | Login admin; ir a Workpanel | Home operativo claro | Workpanel | Default shell sigue `/discover` — ¿confuso? | FULL+NAV | Alta |
| A02 | Admin | Menú completo | `/workpanel` | Sidebar expandido | Solo producto-final; sin CRM/billing | Nav sections | DEMO_SECTION ocultas | NAV | Alta |
| A03 | Admin | Workpanel | `/workpanel` | Con métricas | Densidad, badges real/synthetic, CTAs | Metric cards, sections | Depende seeds enterprise | FULL+DATA | Alta |
| A04 | Admin | Workpanel vacío/error | `/workpanel` | Backend down o DB vacía | ErrorState / empty honesto | Error/Empty | — | ERR+EMPTY | Alta |
| A05 | Admin | Reportes hub | `/reports` | Hub simples/complejos | Unificación visual | Reporting hub | Rutas paralelas simple/complex | FULL | Alta |
| A06 | Admin | Reporte simple | `/simple-reports` | Abrir + ejecutar un reporte con data | Tabla, filtros, export si hay | Simple reports | Ownership/org isolation | FULL+DATA | Alta |
| A07 | Admin | Reporte complejo | `/complex-reports` | Idem warehouse | Claridad métricas warehouse | Complex reports | Queries costosas | FULL+DATA | Alta |
| A08 | Admin | Org hub | `/organizations/:id` | Org activa del seed | Jerarquía hub | Org hub | Onboarding complexity | FULL | Alta |
| A09 | Admin | Miembros (gestión usuarios org) | `/organizations/:id/members` | Listado miembros | Tabla, roles, invitaciones CTA | Data table, badges | Closest to “user mgmt” | FULL+DATA | Alta |
| A10 | Admin | Invitar miembro | `/organizations/:id/invitations` | Form invitaciones | Validaciones email/rol | Form | — | FORM+VAL | Alta |
| A11 | Admin | Roles org | `/organizations/:id/roles` | Listado | Claridad permisos | Table | Complejidad demo | FULL | Media |
| A12 | Admin | Org settings | `/organizations/:id/settings` | Vista settings | Consistencia con Settings global | Forms | — | FULL | Media |
| A13 | Admin | Crear org | `/organizations/new` | Form create | Validación; UX | FormPage | — | FORM+VAL | Media |
| A14 | Admin | Catalog hub | `/catalog` | Hub publishing | Claridad ciclo catálogo | Hub | Tres paquetes densos | FULL | Alta |
| A15 | Admin | Review inbox | `/catalog-review` | Listado reviews | Tabla, estados, badges | Table, StatusBadge | — | FULL+DATA | Alta |
| A16 | Admin | Review detalle | `/catalog-review/:id` | Abrir ítem | Acciones approve/reject | Detail + actions | Permiso publishing.review | FULL+PERM | Alta |
| A17 | Admin | Artist portal tracks | `/artist/tracks` | Listado | CRUD publishing vs warehouse tracks | Tables | Homónimo “tracks” | FULL | Alta |
| A18 | Admin | Artist release new | `/artist/releases/new` | Form creación | Grupos campos, validación | Form | — | FORM+VAL | Alta |
| A19 | Admin | Artist profiles | `/artist-profiles` | Listado | Tabla enterprise kit? | List/table | — | FULL+DATA | Alta |
| A20 | Admin | Artist profile detail | `/artist-profiles/:id` | Detalle | Metadatos + acciones | Detail | — | FULL | Media |
| A21 | Admin | Catalog rights assets | Ruta list assets en catalog-rights | Listado | Consistencia CRUD | enterprise-data-table? | Kit vs ad hoc | FULL | Alta |
| A22 | Admin | Rights detalle / conflicto | conflict o asset detail | Detalle + estado | Badges estado | StatusBadge | — | FULL | Media |
| A23 | Admin | CRUD canciones warehouse | `/tracks` | Como admin steward | Acciones edit/delete visibles; create | Tracks + steward | **POST create siempre 403** | FULL+PERM+DATA | Alta |
| A24 | Admin | Editar canción | `/tracks` o detail | Abrir edit si UI lo permite | Form edición | Form | Validar si UI promete create | FORM | Alta |
| A25 | Admin | Confirmar delete track | `/tracks` | Delete + modal | Nombre elemento + consecuencia | ConfirmDialog | — | MODAL | Alta |
| A26 | Admin | CRUD artistas warehouse | `/artists` | Listado + create/edit si steward | Consistencia con tracks | Artists CRUD | Dual `/artists` vs profiles | FULL+FORM | Alta |
| A27 | Admin | CRUD géneros | `/genres` | Listado + mutaciones | Tabla, filtros, paginación | Genres | — | FULL+DATA | Alta |
| A28 | Admin | Filtros + paginación | `/tracks` o reports | Aplicar filtro + página 2 | UX filtros; chips activos | Filter + pagination | Dispersos | DATA | Alta |
| A29 | Admin | Badges / estados | Workpanel o review | Varios estados | Legibilidad color+texto | StatusBadge, DataSourceBadge | Mock sin etiqueta | FULL | Alta |
| A30 | Admin | Settings admin | `/settings` | Tabs admin/engineer | Tabs técnicos visibles | Settings | — | FULL+PERM | Media |
| A31 | Admin | Deep-link CRM bloqueado | `/crm` | Sin presentationMode | module-unavailable | Error page | No reactivar en demo | ERR+PERM | Media |
| A32 | Admin | Acceso denegado org | `/access-denied` o members sin perm | Forzar sin permiso | Claridad mensaje | Access denied | — | ERR+PERM | Media |
| A33 | Admin | Workpanel móvil | `/workpanel` | 390px | ¿Usable o “solo desktop”? | Layout | Tablas densas | MOB | Media |
| A34 | Admin | Modal confirm genérico | Cualquier delete | Abrir confirm | Consistencia dialog | ConfirmDialog | — | MODAL | Media |

**Capturas A21–A22:** usar las rutas exactas de `catalog-rights.routes.ts` del entorno (assets/releases/contracts/conflicts). Anotar path real en `NOTES.md` si difiere.

---

## 3. Tabla maestra — Ingeniero de datos

> PocketBase y archivos Parquet **no** son rutas Angular. Se capturan: (1) UI ELT de la SPA, (2) opcionalmente UI admin PocketBase externa, (3) Explorer sobre DuckDB.

| N.º | Rol | Pantalla / módulo | Ruta / herramienta | Acción o estado | Qué debemos revisar | Componentes visibles | Posibles problemas (código) | Tipo | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | Engineer | Login → área datos | `/login` → `/elt-pipeline` | Login engineer | Home técnico claro | ELT page | — | FULL+NAV | Alta |
| E02 | Engineer | Menú | `/elt-pipeline` | Sidebar expandido | ELT, Explorer, Workpanel, Reportes | Nav | — | NAV | Alta |
| E03 | Engineer | ELT dashboard | `/elt-pipeline` | Vista inicial | Claridad flujo Medallion | Pipeline UI | Timeline **parcialmente teatral** | FULL | Alta |
| E04 | Engineer | ELT en ejecución | `/elt-pipeline` | Disparar import (`POST /stats/import`) | Feedback progreso vs cosmético | Progress/timeline | Request bloqueante | LOAD+DATA | Alta |
| E05 | Engineer | ELT éxito | `/elt-pipeline` | Post-import OK | Resumen cargas; timestamps | Status, loads | Depende PB creds | DATA | Alta |
| E06 | Engineer | ELT error | `/elt-pipeline` | Credenciales PB mal / offline | Error accionable | ErrorState | — | ERR | Alta |
| E07 | Engineer | Synthetic load | `/elt-pipeline` | Ejecutar synthetic si UI lo expone | Badge **synthetic** visible | Actions | No confundir con PB real | DATA+PERM | Alta |
| E08 | Engineer | Fuentes / warehouse status | `/elt-pipeline` o status embebido | Ver estado fuentes | PocketBase vs parquet vs DuckDB etiquetados | Status panels | — | FULL | Alta |
| E09 | Engineer | PocketBase admin | `POCKETBASE_URL` (externo) | Abrir colección `datasets` | Evidencia fuente real | PB UI | **Fuera de Angular** | FULL | Alta |
| E10 | Engineer | Parquet evidencia | FS `data/bronze`, `data/silver` | Listar archivos post-pipeline | Existen parquet (o documentar ausencia) | Explorer OS | Gitignored; puede estar vacío | DATA | Alta |
| E11 | Engineer | DuckDB evidencia | `data/warehouse/voxmetrik.duckdb` o UI | Confirmar DW existe | Path coherente con docs | File / UI | Ausente en repo limpio | DATA | Alta |
| E12 | Engineer | Warehouse Explorer | `/explorer` | Listar tablas | Legibilidad dims/facts/aggs | Explorer tables | — | FULL+DATA | Alta |
| E13 | Engineer | Explorer preview | `/explorer` | Preview `dim_track` o `fact_streaming` | Límites filas; no freeze UI | Preview table | Preview costoso | DATA | Alta |
| E14 | Engineer | Explorer tabla vacía/error | `/explorer` | Tabla inexistente o error | Manejo error | Error | — | ERR | Media |
| E15 | Engineer | Calidad / loads history | `/elt-pipeline` + loads | Historial `ctl_*` / loads API | Utilidad real del historial | Loads list | — | DATA | Alta |
| E16 | Engineer | Workpanel post-ELT | `/workpanel` | Métricas tras carga | Números coherentes con import | Metrics | Mezcla app_* + warehouse | FULL | Alta |
| E17 | Engineer | Analytics / reportes | `/complex-reports` | Un reporte warehouse | Trazabilidad a tablas | Report UI | — | FULL | Alta |
| E18 | Engineer | Redirect analytics legacy | `/analytics` | Abrir | Debe ir a Workpanel | Redirect | UI analytics muerta en disco | FULL | Media |
| E19 | Engineer | Platform ops (opcional) | `/platform-ops` | Si tiene acceso | ¿Útil en demo corta? | Ops dashboard | Fuera nav primario | FULL | Baja |
| E20 | Engineer | Audio unresolved | `/platform-ops/audio-unresolved` | Listado | Relación con playback demo | Table | — | FULL | Baja |
| E21 | Engineer | Denied listener tools | `/elt-pipeline` como `user` | Deep-link | 403 | Error | engineerGuard | ERR+PERM | Alta |
| E22 | Engineer | ELT móvil | `/elt-pipeline` | 390px | Legibilidad proceso | Layout | Probable desktop-first | MOB | Baja |

---

## 4. Capturas transversales (todos los roles)

| N.º | Rol | Pantalla | Ruta | Acción | Revisar | Tipo | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X01 | Todos | 404 | `/ruta-inexistente-xyz` | Abrir | NotFound vs redirect discover | ERR | Media |
| X02 | Todos | 403 page | `/error/403` | Abrir directo | Copy i18n | ERR | Baja |
| X03 | Todos | Player + CRUD | Admin en `/tracks` con player | Play mientras edita | ¿Player estorba en operativo? | FULL | Media |
| X04 | User+Admin | ES vs EN pair | `/discover` y `/workpanel` | Toggle idioma | Keys faltantes | FULL | Alta |

---

## 5. Matriz: qué tipo de evidencia aporta cada captura

| Necesidad de evidencia | Capturas |
|------------------------|----------|
| Pantalla completa | U03, U07, U13, A03, A05, E03, E12 |
| Menú desplegado | U05, A02, E02 |
| Formularios abiertos | U20, A10, A13, A18, A24 |
| Modales | U20, A25, A34 |
| Registros existentes | U07, U18, A06, A09, E12 |
| Tablas vacías | U08, U22, A04 |
| Validaciones | U20, A10, A18 |
| Errores | U02, U17, U30, A04, E06, E21 |
| Carga | U04, E04 |
| Móvil / tablet | U32, U33, A33, E22 |
| Permitido vs bloqueado | U10, U12, U30, U31, A23, A31, E21 |
| Fuentes datos externas | E09, E10, E11 |
| Duplicación UX | U23+U24, U26+U27 |

---

## 6. Prioridad de sesión de captura (orden práctico)

### Sesión 1 — Usuario (obligatoria)
U01–U09, U13–U24, U26–U28, U30, U32

### Sesión 2 — Administrador (obligatoria)
A01–A09, A14–A17, A23–A29, A05–A07

### Sesión 3 — Ingeniero (obligatoria)
E01–E08, E12–E17, E21 + E09–E11 (evidencia datos)

### Sesión 4 — Bordes (recomendadas)
U10–U12, U25, U31, A31–A34, E18–E20, X01–X04

---

## 7. Plantilla `NOTES.md` (copiar a evidence/)

```markdown
# Notas de revisión visual — VOXMETRIKS

Fecha:
Revisor:
Build / commit (si aplica):
Cuentas usadas:

## Errores al abrir pantallas
| N.º captura | Error observado | Consola / network |

## Diferencias código vs runtime
| Expectativa (checklist) | Observado |

## Hallazgos UX (breves)
-
```

---

## 8. Relación con la auditoría técnica

Esta checklist **no** sustituye la clasificación MANTENER/ELIMINAR. Sirve para:

1. Validar calidad visual real antes de fusionar/eliminar.
2. Confirmar empty/error/loading inconsistentes (design proposal).
3. Detectar pantallas “existen en código” pero rotas o vacías en runtime.

Tras capturas + revisión externa → volver al plan de simplificación con evidencia.

---

**No se generaron imágenes en esta fase.**  
**No modificar UI hasta aprobación post-debate.**
