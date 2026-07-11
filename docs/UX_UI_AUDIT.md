# VOXMETRIKS — Auditoría UX/UI Enterprise (Fase 2)

**Fecha:** 2026-07-05  
**Rol:** Lead Product Designer (referencia: Spotify · Notion · Linear)  
**Alcance:** Sistema visual completo — jerarquía, espaciado, tipografía, componentes, motion, accesibilidad  
**Estado:** Solo documentación. **No se implementaron correcciones.**

**Relacionado:** [FUNCTIONAL_AUDIT.md](./FUNCTIONAL_AUDIT.md) (Fase 1)

---

## Metodología

Recorrido de experiencia pantalla por pantalla desde la perspectiva de diseño de producto premium:

1. Evaluación visual de tokens, componentes compartidos y patrones de interacción.
2. Comparación entre módulos **enterprise** (`features/`) vs **legacy** (`packages/`).
3. Inventario del design system existente vs. desviaciones.
4. Verificación de principios: consistencia, jerarquía, feedback, motion, accesibilidad.

**Capturas:** Se intentó generar screenshots automatizados (`docs/audit-screenshots/`). Playwright no tenía browsers instalados en el entorno de auditoría. La tabla de capturas recomendadas al final indica qué generar manualmente para validación visual.

### Leyenda de prioridad

| Icono | Nivel | Criterio visual |
|-------|-------|-----------------|
| 🔴 | Crítico | Rompe continuidad de producto; parece otra app; bloquea percepción premium |
| 🟠 | Alto | Inconsistencia visible entre módulos; jerarquía confusa; feedback ausente |
| 🟡 | Medio | Desviación de escala; pulido incompleto; deuda de sistema |
| 🟢 | Bajo | Refinamiento; ya alineado o marginal |

---

## Diagnóstico ejecutivo (Lead Designer)

### Lo que ya transmite calidad
- **Paleta dark Spotify-adjacent** bien definida (`#121212`, `#181818`, acento `#1ed896`).
- **Shell coherente:** sidebar negro, player fijo con blur, layout persistente.
- **Motion system** (`styles/motion.css`) con tokens, easing unificado y `prefers-reduced-motion`.
- **Tema claro** (Slate Mist) con overrides extensos — señal de intención enterprise.
- **Componentes enterprise** (`metric-card`, `chart-widget`, `empty-state`, `table-widget`) más pulidos que legacy.
- **Microinteracción favorito** (`vm-fav-pop`) y filas con ecualizador al reproducir.

### Lo que rompe la sensación “un solo equipo”
1. **Dos familias de KPI cards** con radios, hover y tipografía distintos.
2. **Tres escalas de título H1** en la misma sesión (1.375rem · 1.75rem · clamp 2rem).
3. **Espaciado no sistemático** — mezcla rem arbitrarios vs. escala 4-8-12-16 propuesta.
4. **Sin sistema de toast global** — feedback de acciones inconsistente.
5. **Capa legacy** (analytics, trending, comparatives) con CSS propio vs. tokens enterprise.
6. **Estilos inline en componentes** (`media-card`, `track-row`, `kpi-card`) duplican y compiten con CSS global.

**Veredicto PO/Design:** La base es sólida (~70% coherencia). Falta **formalizar el design system** y **eliminar variantes legacy** para alcanzar sensación SaaS premium comparable a Spotify.

---

## Inventario Design System (estado actual)

### Colores — tokens existentes

| Token | Valor dark | Uso |
|-------|------------|-----|
| `--bg-base` | `#0a0a0a` | Fondo app |
| `--spotify-base` | `#121212` | Superficies |
| `--spotify-card` | `#181818` | Cards |
| `--spotify-card-hover` | `#282828` | Hover cards |
| `--accent` / `--color-primary` | `#1ed896` | CTA, links, charts |
| `--accent-hover` | `#1fdf8f` | Hover CTA |
| `--text` | `#ffffff` | Texto principal |
| `--text-muted` | `rgba(255,255,255,0.45)` | Secundario |
| `--shell-sidebar` | `#000000` | Sidebar |
| `--shell-player` | `rgba(18,18,18,0.88)` | Player |
| `--color-danger` | `#ef4444` | Errores |
| `--purple` / comparatives | `#a855f7`, `#7c3aed` | Analytics legacy |

**Gap 🔴 DS-01:** Colores semánticos no consolidados — purple usado en trending Y comparatives con distintos hex en badges.

### Tipografía — escala actual vs. objetivo

| Rol | Objetivo DS | Realidad en app | Pantallas afectadas |
|-----|-------------|-----------------|---------------------|
| Display | 32–40px / 700 | `clamp(1.5rem, 2.4vw, 2rem)` solo enterprise | Dashboard, Destacadas |
| H1 | 28px / 700 | **1.375rem** (22px) global `.vx-page-header` | History, Comparatives |
| H1 | 28px / 700 | **1.75rem** (28px) catalog `.page-title` | Tracks, Artists, ELT |
| H1 | 28px / 700 | **1.75rem–2rem** heroes | Liked, Users, Artist detail |
| H2 | 20px / 700 | **1.25rem** home rails | Inicio |
| Body | 14–16px | 0.8125–0.875rem mezclado | Global |
| Caption | 12px | 0.65–0.75rem uppercase labels | Tablas, KPIs |
| Label | 11px caps | 0.65rem `letter-spacing: 0.07–0.14em` | Enterprise eyebrow |

**Hallazgo 🔴 TYPE-01:** No existe escala tipográfica única. El usuario percibe “salto” al pasar de Inicio → Catálogo → Centro analítico.

**Familia:** Inter (body) + JetBrains Mono (métricas, meta) — decisión correcta y premium ✓

### Espaciado — escala objetivo vs. real

| Token objetivo | px | Tokens actuales |
|----------------|-----|-----------------|
| 4 | 4px | — (no existe) |
| 8 | 8px | `--spacing-md: 0.5rem` parcial |
| 12 | 12px | `--spacing-lg: 0.875rem` (14px) ⚠️ |
| 16 | 16px | `--page-pad-x: 1.125rem` (18px) ⚠️ |
| 24 | 24px | `--section-gap: 0.875rem` (14px) ⚠️ |
| 32 | 32px | ad-hoc `1.25rem`, `1.35rem`, `1.5rem` |
| 48 | 48px | — |
| 64 | 64px | — |

**Hallazgo 🔴 SPACE-01:** La escala 4·8·12·16·24·32·48·64 **no está implementada**. Valores rem fraccionados (0.625rem, 0.875rem, 1.125rem) generan ritmo visual irregular.

### Motion — tokens (bien definidos ✓)

| Token | Valor |
|-------|-------|
| `--motion-duration-fast` | 150ms |
| `--motion-duration-normal` | 220ms |
| `--motion-duration-slow` | 320ms |
| `--motion-ease-standard` | cubic-bezier(0.22, 1, 0.36, 1) |
| Route enter | fade + translateY 8px |

**Gap 🟡 MOT-01:** Hover en cards usa `-2px`, `-4px` y `scale(1.02)` según componente — no unificado.

### Componentes — inventario

| Componente | Existe | Unificado | Notas |
|------------|--------|-----------|-------|
| `metric-card` | ✓ | Enterprise | radius 14px, glass |
| `kpi-card` | ✓ | Home/Legacy | radius 8px; **CSS duplicado** inline + `.css` |
| `media-card` | ✓ | Streaming | 184px fijo; estilos inline |
| `track-row` | ✓ | Listas | Grid 7 cols; estilos inline |
| `glass-panel` | ✓ | Global | blur 14px |
| `empty-state` | ✓ | Parcial | Enterprise sí; catálogo usa otro `.empty-state` |
| `chart-widget` | ✓ | Enterprise | ECharts |
| `table-widget` | ✓ | Enterprise | Mat paginator |
| `data-table` / `.vx-table` | ✓ | Catálogo | Dos nombres, estilos similares |
| `confirm-dialog` | ✓ | Global | z-index 1200 |
| CRUD modal | ✓ | Catálogo | z-index 1000 ⚠️ |
| **Toast global** | ✗ | — | Solo `prefs-toast` en Settings |
| **Breadcrumb** | ✗ | — | — |
| **FAB** | ✗ | — | — |
| Button system | Parcial | 5+ variantes ad-hoc | |

---

## Auditoría visual por pantalla

Escala por criterio: ✅ Cumple · ⚠️ Parcial · ❌ No cumple

### Inicio / Dashboard de consumo (`/discover`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ✅ Mejor pantalla del producto — hero gradient, rails Spotify |
| Diseño general | ✅ Sidebar + player integrados |
| Coherencia | ⚠️ Banda KPI usa `kpi-card`; widgets SVG custom |
| Equilibrio | ✅ Denso pero jerárquico |
| Profesional | ✅ |

**Observaciones:**
- Hero con glow verde + chips — premium ✓
- KPI strip 8 tarjetas compiten con widgets — **jerarquía saturada** 🟠 VIS-DISC-01
- Rails horizontales consistentes (`horizontal-section`) ✓
- Insight strip cards pequeñas — buen contraste con KPIs ✓
- Skeleton `@defer` placeholder — buen rendimiento percibido ✓

**Captura recomendada:** `docs/audit-screenshots/discover.png`

---

### Centro analítico (`/dashboard`) — Dashboard Analytics enterprise

| Criterio | Eval |
|----------|------|
| Identidad visual | ✅ Lenguaje enterprise distinto pero dentro de paleta |
| Diseño general | ✅ |
| Coherencia | ⚠️ `metric-card` ≠ `kpi-card` del Home |
| Equilibrio | ✅ Grid 4 KPIs + charts 2col |
| Profesional | ✅ |

**Observaciones:**
- Eyebrow uppercase + H1 clamp — **mejor jerarquía H1 del producto** 🟢
- Charts con `empty-state` integrado ✓
- Gap secciones `1.35rem` vs Home `0.875rem` — **ritmo distinto** 🟡 VIS-DASH-01
- Max-width 1440px centrado — sensación producto maduro ✓

**Captura:** `docs/audit-screenshots/dashboard.png`

---

### Canciones catálogo (`/tracks`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ⚠️ Parece “admin CRUD” vs. streaming |
| Diseño general | ✅ Usa `catalog-page-shared` |
| Coherencia | ⚠️ H1 1.75rem vs 1.375rem otras páginas |
| Equilibrio | ✅ Header + search + tabla |
| Profesional | ⚠️ |

**Observaciones:**
- Tabla densa con virtual scroll — funcional, poco “Spotify” 🟠 VIS-TRK-01
- Botones CRUD steward rompen fantasy consumer para admins — OK con badge readonly
- Paginación numérica consistente con artists/genres ✓
- Error card roja bien diseñada ✓

**Captura:** `docs/audit-screenshots/tracks-catalog.png`

---

### Canciones destacadas (`/insights/tracks`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ⚠️ Grid cards ≠ tabla catálogo |
| Diseño general | ✅ Media cards |
| Coherencia | ❌ **Hardcoded ES** en hero; no i18n |
| Equilibrio | ✅ |
| Profesional | ⚠️ |

**Observaciones:**
- Mismo `media-card` que Home — continuidad ✓
- Spinner propio `tracks-spin 0.7s` vs `vm-shimmer` elsewhere 🟡
- Sin page header estándar `.vx-page-header` — **ruptura de plantilla** 🟠 VIS-FT-01

**Captura:** `docs/audit-screenshots/tracks-featured.png`

---

### Artistas (`/artists`) + Detalle (`/artists/:id`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ⚠️ Catálogo admin pattern |
| Coherencia | ✅ Shared catalog CSS |
| Hero detalle | ✅ Gradiente + avatar — premium |
| Profesional | ⚠️ |

**Observaciones:**
- Listado = tabla como tracks ✓ consistencia interna
- Detalle artista más cinematográfico que listado — **salto intencional aceptable** 🟢
- Load more button ≠ paginación listado — inconsistencia interacción 🟡

**Captura:** `docs/audit-screenshots/artists.png`

---

### Álbumes (`/albums`)

| Criterio | Eval |
|----------|------|
| Pantalla | ❌ **No existe** |

**Hallazgo 🔴 VIS-ALB-01:** KPI e iconografía `album` en Home sin superficie visual. Incumple mapa de auditoría solicitado.

---

### Playlists (`/playlists`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ✅ Grid cards + hero detalle |
| Coherencia | ✅ Gradients COVERS array consistente |
| Modales CRUD | ⚠️ Mismo modal catálogo |
| Profesional | ✅ |

**Observaciones:**
- Hero detalle playlist estilo Spotify ✓
- Cards listado con skeleton pulse ✓
- Create/edit modal — falta animación entrada unificada 🟡

**Captura:** `docs/audit-screenshots/playlists.png`

---

### Favoritos (`/liked`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ✅ Hero heart + gradient verde |
| Coherencia | ✅ `track-row` + `glass-panel` |
| Empty state | ✅ Icono + CTA explorar |
| Profesional | ✅ |

**Observaciones:**
- Una de las pantallas más cohesionadas con identidad streaming 🟢
- Play all button blanco sobre verde — alineado `--play-btn-*` ✓

**Captura:** `docs/audit-screenshots/liked.png`

---

### Historial (`/history`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ✅ Tabs + timeline |
| Coherencia | ✅ `vx-page-header` |
| Empty states | ✅ Con CTAs por tab |
| Profesional | ✅ |

**Observaciones:**
- Tab bar custom — no reutiliza componente Tabs global 🟡 VIS-HIS-01
- Mezcla badges `local` / `mixed` — buena honestidad de datos ✓

**Captura:** `docs/audit-screenshots/history.png`

---

### Comparativas (`/comparatives`)

| Criterio | Eval |
|----------|------|
| Identidad visual | ⚠️ Purple accent dominante vs verde global |
| Coherencia | ⚠️ Insight cards propias ≠ kpi-card |
| Heatmap | ✅ Sofisticado |
| Profesional | ⚠️ Parece módulo analytics separado |

**Hallazgo 🟠 VIS-CMP-01:** Badge `insight-badge` purple compite con brand green — usuario siente “otro producto analytics”.

**Captura:** `docs/audit-screenshots/comparatives.png`

---

### Analítica legacy (`/analytics`) + Streaming insights (`/insights/analytics`)

| Pantalla | Identidad | Problema principal |
|----------|-----------|-------------------|
| `/analytics` | Legacy div KPIs | Cards custom `.kpi-row .kpi-card` — hover distinto |
| `/insights/analytics` | Enterprise charts | Mejor alineación con `/dashboard` |

**Hallazgo 🔴 VIS-AN-01:** Tres experiencias analíticas visuales (`/dashboard`, `/insights/analytics`, `/analytics`) sin sistema unificado de widgets.

**Capturas:** `analytics-legacy.png`, `analytics-insights.png`

---

### Tendencias (`/trending`) — incluido en espíritu analytics

- Hero #1 cinematográfico — **highlight premium** 🟢
- Textos hardcoded ES en hero (“Líder del ranking”, “Reproducir”) 🟠
- Sparkline decorativo sin leyenda — bonito pero no informa 🟡

---

### ELT Pipeline (`/elt-pipeline`)

| Criterio | Eval |
|----------|------|
| Identidad | ⚠️ Engineer dashboard |
| Coherencia | ⚠️ H1 1.75rem catalog style |
| Profesional | ✅ Para rol engineer |

**Captura:** `docs/audit-screenshots/elt-pipeline.png` (admin)

---

### Explorer (`/explorer`)

- Tabla + paginación 8 — consistente engineer tooling ✓
- Skeleton pulse 1.5s — más lento que `vm-shimmer` 1.4s 🟡

---

### Configuración (`/settings`)

- Tabs propios — tercer patrón de tabs 🟠 VIS-SET-01
- **Único toast inline** `.prefs-toast` — no reutilizable 🟠 TOAST-01
- Forms bien espaciados ✓

**Captura:** `docs/audit-screenshots/settings.png`

---

### Player (global)

| Criterio | Eval |
|----------|------|
| Integración | ✅ Glass blur, altura 88px fija |
| Tipografía | ✅ Consistente shell tokens |
| Hover progreso | ✅ Thumb scale — Spotify-like |
| Responsive | ⚠️ Grid 3 cols colapsa en mobile |
| Hardcode | 🟡 `#1ed896` literal en progress fill |

**Hallazgo 🟡 PLAY-UI-01:** Now Playing expandible es premium; en viewport estrecho controles pueden comprimirse.

**Captura:** `docs/audit-screenshots/player-discover.png` (con track reproduciendo)

---

## Jerarquía visual — auditoría transversal

### Orden de lectura ideal vs. actual

| Zona | Debe dominar | Compite con | Prioridad |
|------|--------------|-------------|-----------|
| Home | Hero greeting | 8 KPIs inmediatos | 🟠 |
| Catálogo | Título + búsqueda | page-meta pill mono | 🟡 |
| Dashboard enterprise | H1 + KPI row | Warning banner | 🟢 |
| Track row | Título canción | Popularidad bar + energy | 🟡 |
| Sidebar | Sección activa | 6 secciones uppercase | 🟢 |

**Hallazgo 🟠 HIER-01:** En Home, KPI strip y hero compiten al mismo nivel — el ojo no tiene un único foco post-greeting.

---

## Cards — matriz comparativa

| Variante | Ancho | Radius | Padding | Hover | Shadow |
|----------|-------|--------|---------|-------|--------|
| `media-card` | 184px fijo | 10px / cover 7px | 0.7rem | bg hover shell | cover shadow |
| `kpi-card` | flex grid | 8px | 0.875–1rem | translateY **-4px** | glow verde |
| `metric-card` | grid 1fr | **14px** | 1.25rem | translateY **-2px** | shadow-glow |
| `glass-panel` | 100% | 8px (--radius-lg) | var(--panel-pad) | border only | shadow-sm |
| Legacy `.kpi-card` div | auto | 8px | variable | bg spotify-card-hover | none |
| Playlist card | grid | ~12px | custom | scale subtle | module CSS |

**Hallazgo 🔴 CARD-UI-01:** Mínimo **4 familias de cards** con hover y radius distintos. Usuario percibe inconsistencia al navegar Home → Dashboard → Analytics.

**Corrección propuesta:** Unificar en `VmCard` con variants: `elevated | flat | media | metric`.

---

## Botones — auditoría

| Variante | Altura approx | Radius | Estados | Ubicación |
|----------|---------------|--------|---------|-----------|
| `.btn-primary` | ~38px | 8px | hover lift, disabled opacity | Catálogo |
| `.btn-secondary` | ~38px | 8px | hover bg | Catálogo |
| `.btn-danger` | ~38px | 8px | hover | Catálogo |
| `.btn-icon` | 28×28 | 6px | color bg | Tabla actions |
| `.fav-btn` | 32×32 (28 sm) | 50% | pop animation | Global |
| `.play-all-btn` / `.hero-play` | custom | custom | — | Liked, Trending |
| `.ghost-btn` | custom | custom | — | History |
| `.empty-action-btn` | ~32px | `--radius` 6px | border hover | EmptyState |
| `.link-btn` | text | — | underline hover | Liked empty |
| Player `.play-btn` | 36px circle | 50% | disabled | Player |

**Hallazgo 🔴 BTN-01:** No existe **Button primitive** documentado. Mínimo 10 variantes ad-hoc.

**Hallazgo 🟡 BTN-02:** Primary button text color `#000` en global pero `var(--text)` en catalog-shared — posible inconsistencia tema claro.

**Focus visible:** Transitions globales ✓; ring focus no uniforme en todos los botones 🟡 A11Y-01

---

## Iconografía

| Aspecto | Estado |
|---------|--------|
| Librería | SVG inline + `IconRenderService` + registry |
| Tamaños | 14, 16, 18, 22, 24, 32, 48 dispersos |
| Stroke | Mayoría stroke-width 2 ✓ |
| Nav icons | 18×18 inline en layout |
| Problema | Emojis en genre chip Home (`♪`) mezclados con SVG 🟡 ICON-01 |

---

## Hover — feedback audit

| Elemento | Feedback | Suavidad |
|----------|----------|----------|
| Sidebar nav | bg hover + indicator | ✅ 150ms |
| Media card | bg + cover shadow | ✅ |
| Track row | bg green tint | ✅ |
| Table row | row-hover | ✅ |
| KPI card | translateY -4px | ⚠️ Agresivo vs metric -2px |
| Glass panel | border only | ✅ Sutil |
| Pagination | border accent | ✅ |

**Regla cumplida:** No hay parpadeos ni animaciones exageradas en general ✓

---

## Animaciones — inventario

| Tipo | Implementación | Consistencia |
|------|----------------|--------------|
| Route change | `routeFadeAnimation` 220ms | ✅ Global |
| Page enter | `.vm-content-ready`, `.vm-fade-in` | ⚠️ No todas las páginas |
| Skeleton | shimmer / pulse / skel gradient | ⚠️ 3 variantes |
| Chart draw | `vm-chart-draw` | ✅ Enterprise |
| Favorito | `vm-fav-pop` | ✅ |
| Modal | backdrop blur | ⚠️ Sin animate enter |
| Sidebar | width collapse 320ms | ✅ |
| Cover load | `coverFade 0.3s ease` | ✅ media-card only |

**Hallazgo 🟡 MOT-02:** Modales aparecen sin scale/fade — sensación menos premium que Linear/Notion.

---

## Microinteracciones

| Acción | Feedback visual | Inmediato |
|--------|-----------------|-----------|
| Favorito | ❤ pop + color | ✅ |
| Play track | Row highlight + eq bars | ✅ |
| Crear playlist | Modal → reload list | ⚠️ Sin toast |
| Eliminar | Confirm dialog | ✅ dialog |
| Guardar settings | Inline toast | ⚠️ Solo aquí |
| Login | — | ⚠️ Sin toast éxito |
| Logout | Redirect | ⚠️ Sin despedida |
| Add to playlist | Dropdown | ⚠️ Sin confirm toast |
| CRUD track | Modal close + list refresh | ⚠️ Sin toast |

**Hallazgo 🔴 MICRO-01:** Acciones CRUD silenciosas — usuario no sabe si guardó excepto viendo la lista actualizada.

---

## Loading states

| Pantalla | Skeleton | Spinner | Empty-state component |
|----------|----------|---------|----------------------|
| Home | ✅ skel rails/KPI | — | ✅ error block |
| Dashboard enterprise | ✅ metric skeleton | — | ✅ |
| Catálogo | ✅ table skel rows | — | ✅ inline |
| Destacadas | — | ✅ spinner | ✅ EmptyState |
| Liked | ✅ row skel | — | ✅ custom |
| Trending | ✅ skeleton-card grid | — | — |
| Comparatives | ✅ skeleton rows | — | — |
| Analytics legacy | ✅ shimmer | — | partial |

**Hallazgo 🟡 LOAD-01:** Spinner vs skeleton no sigue regla única (skeleton para layout, spinner para inline).

**Hallazgo 🟢 LOAD-02:** `@defer (on viewport)` en Home — excelente rendimiento percibido.

---

## Estados vacíos

| Módulo | Ilustración | Mensaje | Explicación | Acción |
|--------|-------------|---------|-------------|--------|
| `empty-state` component | Icon SVG | ✅ i18n | ✅ | Retry / clear search |
| Catálogo `.empty-state` | Icon opacity 0.4 | ✅ | ✅ small | — |
| Liked | Heart icon | ✅ | ✅ hint | ✅ Explorar |
| History tabs | Tab icons | ✅ | ✅ hints | ✅ CTAs |
| Playlists | — | ✅ | ✅ | Create |

**Hallazgo 🟢 EMPTY-01:** Mayoría cumple brief — no solo "No hay datos".

**Gap 🟡:** Enterprise empty-state sin ilustración grande estilo Spotify/Notion — solo icon 32px.

---

## Mensajes de error

| Tipo | Presentación | Amigable |
|------|--------------|----------|
| API backend | i18n `errors.backendConnection` | ✅ |
| Partial analytics | inline-warning + retry | ✅ |
| Form modal | `apiFormError()` | ✅ |
| Console | stack traces | ✅ no expuesto UI |
| EmptyState error | retry button | ✅ |

**Hallazgo 🟢 ERR-01:** No se detecta exposición de Error 500 / stacktrace al usuario.

**Gap 🟡:** Sin acción "Contactar soporte" en errores persistentes.

---

## Toasts

**Hallazgo 🔴 TOAST-01:** **No existe componente toast global.**

Única implementación: `.prefs-toast` en Settings (ok/error inline).

Impacto: crear/editar/eliminar/favorito/playlist no tienen feedback efímero consistente.

**Corrección propuesta:** `VmToastService` — bottom-right, 3s, slide-up 220ms, variants success/error/info.

---

## Modales

| Aspecto | CRUD modal | Confirm dialog |
|---------|------------|----------------|
| Overlay | rgba 0.65 blur 4px | rgba 0.55 blur 4px |
| z-index | 1000 | 1200 |
| Escape | ⚠️ verificar por modal | ✅ |
| Click outside | ✅ backdrop | ✅ |
| Animación entrada | ❌ | ❌ |
| Responsive | padding 1rem | padding 1rem |

**Hallazgo 🟠 MOD-01:** z-index inconsistente; confirm siempre encima — OK pero documentar capas.

---

## Sidebar — comparación Spotify

| Criterio | VOXMETRIKS | Spotify ref |
|----------|------------|-------------|
| Fondo negro puro | ✅ | ✅ |
| Ancho 240px | ✅ ~240 | ✅ |
| Collapse a iconos | ✅ 72px | ✅ |
| Label secciones uppercase | ✅ | ✅ |
| Active indicator | ✅ bar + bg | ✅ |
| Hover sutil | ✅ | ✅ |
| Icono + label alineación | ✅ | ✅ |

**Hallazgo 🟢 SB-01:** Sidebar es el componente más alineado con referencia Spotify.

**Gap 🟡:** 17+ items sin scroll grouping sticky — lista larga en laptop.

---

## Tablas

| Variante | Header style | Row hover | Paginación |
|----------|--------------|-----------|------------|
| `data-table` catalog | 0.72rem caps | green tint | page-btn |
| `table-widget` | Mat paginator | component | 8/page |
| `vx-table` global | 0.65rem caps | row-hover | — |

**Hallazgo 🟠 TBL-01:** Tres implementaciones visuales de tabla.

---

## Dashboard widgets — alineación

| Widget | Alineación grid | Leyendas | Tooltips | Loading |
|--------|-----------------|----------|----------|---------|
| metric-card row | ✅ 4 col | subtitle | — | skeleton |
| chart-widget | ✅ 2 col | ✅ ECharts | ✅ | empty canvas |
| table-widget | ✅ 2 col | headers | — | — |
| Home SVG spark | custom | ❌ | title attr | empty text |
| Comparatives heatmap | custom | ✅ | cell title | skeleton |

**Hallazgo 🟡 CHART-01:** Home usa SVG inline; Dashboard usa ECharts — estilos de ejes distintos.

---

## Responsive

| Breakpoint | Comportamiento | Problemas |
|------------|----------------|-----------|
| Desktop ≥1440 | ✅ | — |
| Laptop 1024–1440 | ✅ sidebar collapse avail | — |
| Tablet 768–1024 | ⚠️ sidebar overlay | KPI 2 col |
| Mobile <768 | ⚠️ | Player grid comprimido 🟠 |
| 480 | KPI 1 col | ✅ |

**Hallazgo 🟠 RESP-01:** Tablas catálogo con scroll horizontal — aceptable pero scrollbars 5px casi invisibles.

**Hallazgo 🟡 RESP-02:** `media-card` 184px fijo — rails OK; grids no reflow a 2 col en mobile.

---

## Accesibilidad

| Criterio | Estado |
|----------|--------|
| Contraste texto/ fondo dark | ✅ Mayoría WCAG AA |
| Contraste `--text-muted` 0.45 | ⚠️ Borderline AA para captions |
| ARIA en player | ✅ labels play/pause |
| ARIA empty-state | ✅ role=status, live |
| ARIA kpi-card | ✅ figure + aria-label |
| Focus keyboard | ⚠️ No visible ring uniforme |
| Tab order modals | ⚠️ trap no verificado |
| Color-only states | ⚠️ Trend positive solo verde |
| Reduced motion | ✅ media query global |

---

## Consistencia global — scorecard

| Dimensión | Score | Nota |
|-----------|-------|------|
| Color / tema | 85% | Tokens fuertes |
| Tipografía | 55% | Escalas múltiples |
| Espaciado | 50% | Sin escala 4px |
| Cards | 45% | 4 familias |
| Botones | 50% | Sin primitive |
| Motion | 75% | Tokens buenos, aplicación parcial |
| Feedback acciones | 40% | Sin toast |
| Loading | 70% | Skeleton presente |
| Tablas | 60% | Triple patrón |
| Player/sidebar | 90% | Mejor logrado |

**Media ponderada UX/UI: ~62%** — base premium, falta sistematización.

---

## Registro de hallazgos priorizado

### 🔴 Críticos

| ID | Pantalla | Componente | Impacto | Corrección propuesta | Mejora esperada | DS |
|----|----------|------------|---------|----------------------|-----------------|-----|
| TYPE-01 | Global | Typography | Salto visual entre módulos | Escala Display/H1/H2/Body/Caption en tokens | Lectura fluida | Typography |
| SPACE-01 | Global | Spacing tokens | Ritmo irregular | `--space-1`…`--space-16` (4px base) | Aire consistente | Spacing |
| CARD-UI-01 | Home/Dashboard/Analytics | Cards | 4 familias cards | Unificar `VmCard` variants | Mismo producto | Cards |
| BTN-01 | Global | Buttons | 10+ botones ad-hoc | `VmButton` primary/secondary/ghost/icon | Clics predecibles | Buttons |
| TOAST-01 | Global | — | CRUD silencioso | Toast service global | Feedback inmediato | Toast |
| VIS-AN-01 | Analytics ×3 | Dashboard widgets | Tres UIs analíticas | Design system charts+KPIs compartido | Continuidad | Charts/KPIs |
| VIS-ALB-01 | Home KPI | kpi-card album | Promesa visual rota | Módulo álbumes o quitar KPI | Honestidad UI | KPIs |

### 🟠 Altos

| ID | Pantalla | Componente | Impacto | Corrección | Mejora | DS |
|----|----------|------------|---------|------------|--------|-----|
| VIS-DISC-01 | Home | KPI strip | Saturación jerárquica | Colapsar KPIs o secondary page | Foco en descubrimiento | Layout |
| VIS-TRK-01 | Tracks | data-table | Sensación admin | Vista dual: tabla + grid opcional | Consumer feel | Tables |
| VIS-FT-01 | Destacadas | page template | Sin header estándar | Usar `vx-page-header` | Coherencia | Layout |
| VIS-CMP-01 | Comparatives | Purple accent | Brand rupture | Mapear a `--accent` o `--color-info` | Una identidad | Color |
| HIER-01 | Home | Hero vs KPIs | Competencia focal | KPI band below fold o carousel | Jerarquía clara | Layout |
| TBL-01 | Global | Tables | 3 estilos | Unificar `VmTable` | Scan consistente | Tables |
| MOD-01 | Modals | z-index/animate | Capas/entrada brusca | Z-scale doc + fade/scale 220ms | Premium modals | Modals |
| MICRO-01 | CRUD | — | Sin confirmación toast | Toast on success/error | Confianza | Toast |
| RESP-01 | Mobile | Player | Controles apretados | Stack player 2 rows <640px | Usable mobile | Player |
| VIS-SET-01 | Settings | Tabs | 3er patrón tabs | `VmTabs` shared | Patrón único | Tabs |

### 🟡 Medios

| ID | Pantalla | Componente | Impacto | Corrección | Mejora | DS |
|----|----------|------------|---------|------------|--------|-----|
| MOT-01 | Cards | hover translate | -2px vs -4px | Token `--hover-lift: 2px` | Hover uniforme | Motion |
| MOT-02 | Modals | — | Entrada abrupta | Animate overlay+panel | Suavidad | Motion |
| LOAD-01 | Global | loaders | spinner vs skeleton | Guía: skeleton layout, spinner inline | Perceived perf | Loading |
| ICON-01 | Home | genre chip | emoji + svg | SVG only | Icon consistency | Icons |
| PLAY-UI-01 | Player | progress | hardcoded hex | `var(--accent)` | Theme safe | Player |
| VIS-DASH-01 | Dashboard | section gap | distinto a Home | `--section-gap: 24px` unified | Ritmo | Spacing |
| VIS-HIS-01 | History | tab-bar | custom tabs | VmTabs | Reuse | Tabs |
| CHART-01 | Home vs Dashboard | SVG vs ECharts | Ejes distintos | Sparkline component shared | Chart consistency | Charts |
| A11Y-01 | Global | focus ring | keyboard nav | `:focus-visible` ring token | A11y AA | A11y |
| EMPTY-01 | Global | empty-state | icon small | Optional illustration slot | Delight | Empty states |

### 🟢 Bajos / Fortalezas

| ID | Nota |
|----|------|
| SB-01 | Sidebar nivel Spotify |
| PLAY-UI-02 | Progress thumb hover excelente |
| ERR-01 | Errores amigables sin stacktrace |
| EMPTY-02 | Empty states con CTAs en mayoría |
| MOT-03 | reduced-motion respetado |
| THEME-01 | Light theme Slate Mist bien pensado |
| LOAD-02 | @defer viewport Home |

---

## Design System propuesto (target Fase 3)

Documentación recomendada en `docs/design-system/` (futuro):

```
tokens/
  colors.css      ← consolidar spotify + semantic
  typography.css  ← Display, H1-H3, Body, Caption, Label
  spacing.css     ← 4px scale
  radius.css      ← sm:4, md:8, lg:12, xl:16
  shadow.css
  motion.css      ← existente, adoptar 100%

components/
  VmButton
  VmCard (media | metric | flat)
  VmInput / VmSearch
  VmTable
  VmTabs
  VmModal
  VmToast
  VmEmptyState
  VmBadge
  VmKpi
  VmChart (wrapper ECharts)
```

### Escala tipográfica objetivo

| Token | Size | Weight | Line-height | Use |
|-------|------|--------|-------------|-----|
| `--text-display` | 32px | 700 | 1.15 | Hero enterprise |
| `--text-h1` | 28px | 700 | 1.2 | Page titles |
| `--text-h2` | 20px | 700 | 1.25 | Section rails |
| `--text-h3` | 16px | 600 | 1.3 | Panel heads |
| `--text-body` | 14px | 400 | 1.45 | Default |
| `--text-caption` | 12px | 400 | 1.4 | Hints |
| `--text-label` | 11px | 600 | 1.2 | Uppercase labels |

### Escala espaciado objetivo

```css
--space-1: 4px;  --space-2: 8px;  --space-3: 12px;  --space-4: 16px;
--space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;
```

---

## Capturas recomendadas

Generar manualmente o con `npx playwright install && node scripts/capture-audit-screenshots.js`:

| Archivo | Ruta | Viewport | Notas |
|---------|------|----------|-------|
| `discover.png` | `/discover` | 1440×900 | Hero + KPIs + rails |
| `dashboard.png` | `/dashboard` | 1440×900 | Enterprise KPIs + charts |
| `tracks-catalog.png` | `/tracks` | 1440×900 | Tabla catálogo |
| `tracks-featured.png` | `/insights/tracks` | 1440×900 | Grid media cards |
| `artists.png` | `/artists` | 1440×900 | Listado |
| `playlists.png` | `/playlists` | 1440×900 | Grid |
| `liked.png` | `/liked` | 1440×900 | Hero + rows |
| `history.png` | `/history` | 1440×900 | Tabs |
| `comparatives.png` | `/comparatives` | 1440×900 | Heatmap |
| `analytics-legacy.png` | `/analytics` | 1440×900 | Legacy KPIs |
| `analytics-insights.png` | `/insights/analytics` | 1440×900 | Enterprise charts |
| `settings.png` | `/settings` | 1440×900 | Tabs settings |
| `player-discover.png` | `/discover` + play | 1440×900 | Player activo |
| `mobile-discover.png` | `/discover` | 390×844 | Responsive |
| `light-theme-discover.png` | `/discover` | 1440×900 | Tema claro |

Ubicación: `docs/audit-screenshots/`

---

## Roadmap sugerido (Fase 3 — implementación)

Prioridad diseño recomendada sin tocar lógica de negocio:

1. **Tokens** — spacing + typography CSS (1–2 días)
2. **VmButton + VmToast** — feedback universal (2 días)
3. **Unificar KPI** — metric-card absorbe kpi-card (2 días)
4. **Page template** — `vx-page-header` obligatorio en todos los módulos (1 día)
5. **VmCard** — media + metric variants (2 días)
6. **Analytics visual merge** — skin compartido dashboard/insights/legacy (3 días)
7. **Modal animation + z-scale** (0.5 día)
8. **Focus rings + contrast audit** (1 día)
9. **Capturas regression** — Playwright visual en CI (1 día)

---

## Criterio de éxito — evaluación actual

| Pregunta | ¿Cumple hoy? |
|----------|--------------|
| ¿Cada pantalla parece del mismo producto? | **Parcial** — streaming sí; analytics/engineer parecen add-ons |
| ¿No hay diferencias visuales injustificadas? | **No** — H1, cards, KPIs, tablas divergen |
| ¿Interacciones consistentes? | **Parcial** — hover OK; toasts/CRUD no |
| ¿Sensación calidad / madurez? | **Parcial-alto** en Home/Player/Sidebar |
| ¿Comparable Spotify/Notion/Linear? | **~65%** — falta sistematización final |

---

## Anexo — archivos visuales clave

| Área | Archivo |
|------|---------|
| Tokens globales | `apps/frontend/src/styles.css` |
| Motion | `apps/frontend/src/styles/motion.css` |
| Catálogo shared | `apps/frontend/src/app/shared/styles/catalog-page-shared.css` |
| Sidebar/Shell | `apps/frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.css` |
| Player | `apps/frontend/src/app/shared/components/player-bar/player-bar.component.css` |
| KPI Home | `apps/frontend/src/app/shared/components/kpi-card/` |
| KPI Enterprise | `apps/frontend/src/app/shared/components/metric-card/` |
| Media card | `apps/frontend/src/app/shared/components/media-card/media-card.component.ts` |
| Empty state | `apps/frontend/src/app/shared/components/empty-state/` |
| Route motion | `apps/frontend/src/app/shared/animations/route.animations.ts` |

---

*Documento generado en Fase 2. Sin cambios de código. Listo para revisión Design + planificación Fase 3 (implementación design system).*
