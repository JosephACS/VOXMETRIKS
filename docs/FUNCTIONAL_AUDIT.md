# VOXMETRIKS — Auditoría Funcional Completa (Fase 1)

**Fecha:** 2026-07-05  
**Rol:** Product Owner  
**Alcance:** Recorrido de producto completo — navegación, botones, listados, estados, coherencia  
**Estado:** Solo documentación. **No se implementaron correcciones.**

---

## Metodología

1. Recorrido lógico como usuario nuevo siguiendo el flujo solicitado: Inicio → Sidebar → módulos → Player → Cerrar sesión.
2. Mapeo de rutas desde `app.routes.ts` y menú lateral (`dashboard-layout.component.ts`).
3. Revisión de templates, servicios, i18n y patrones de paginación/búsqueda/filtros por módulo.
4. Cruce con suite E2E Playwright (`automation/e2e/tests/`).
5. Validación en navegador intentada contra `http://127.0.0.1:4200` — conexión no disponible desde el entorno de auditoría automatizada; hallazgos basados en código + E2E.

### Leyenda de prioridad

| Icono | Nivel | Criterio |
|-------|-------|----------|
| 🔴 | Crítico | Bloquea comprensión, promete algo que no existe, datos engañosos, callejón sin salida |
| 🟠 | Alto | Confusión frecuente, incoherencia entre módulos, pérdida de contexto |
| 🟡 | Medio | Inconsistencia de patrón, UX subóptima, deuda visible |
| 🟢 | Bajo | Pulido, accesibilidad menor, mejoras cosméticas |

---

## Mapa de navegación completo

```
Login (/login)
└── App autenticada (DashboardLayout + PlayerBar persistente)
    ├── Inicio (/discover) [default]
    │   ├── Hero + KPIs resumen
    │   ├── Banda analítica (KPIs + widgets)
    │   │   └── Ver más → /analytics
    │   ├── Recientes → Ver todo → /history
    │   ├── Recomendado para ti → Ver todo → /recommendations
    │   ├── Descubrir → Ver todo → /tracks  ⚠️ (catálogo completo, no rail)
    │   ├── Artistas → Ver todo → /artists
    │   ├── Playlists → Ver todo → /playlists
    │   ├── Géneros → Ver todo → /genres
    │   │   └── Chip género → /tracks?genre_id=&genre_name=
    │   └── Actividad reciente → Ver todo → /history
    │
    ├── PRINCIPAL
    │   ├── Centro analítico (/dashboard)          [enterprise]
    │   ├── Analítica de streaming (/insights/analytics)
    │   └── Canciones destacadas (/insights/tracks) [ranking infinite scroll]
    │
    ├── MÚSICA
    │   ├── Artistas (/artists)
    │   │   ├── Buscar · Filtrar · Ordenar · Paginar (50/pág)
    │   │   └── Detalle (/artists/:id)
    │   │       ├── Reproducir · Favorito · Cargar más canciones
    │   │       └── Sin breadcrumb / volver contextual
    │   ├── Canciones (/tracks)                    [catálogo CRUD]
    │   │   ├── Buscar (debounce 350ms) · Filtro género/artista (query params)
    │   │   ├── Paginar (50/pág) · CRUD (solo steward)
    │   │   └── Detalle (/tracks/:id)
    │   │       ├── Play · Favorito · Añadir a playlist
    │   │       └── Volver → /tracks (no contextual)
    │   ├── Géneros (/genres)
    │   │   ├── Buscar · Paginar (50/pág)
    │   │   └── (sin detalle de género dedicado)
    │   ├── Características de audio (/audio-features)
    │   │   └── Selector de 6 tracks fijos (sin listado completo)
    │   ├── Buscar (/search)
    │   │   ├── Debounce 350ms · Paginación tracks (20/pág)
    │   │   └── Historial → ?q= precargado ✓
    │   ├── Listas (/playlists)
    │   │   ├── Crear · Editar · Eliminar
    │   │   └── Detalle (/playlists/:id)
    │   │       ├── Play all · Añadir/quitar canciones
    │   │       └── Volver a listado
    │   ├── Canciones que te gustan (/liked)
    │   │   └── Lista completa sin paginación
    │   └── Historial (/history)
    │       ├── Pestañas: música | usuario | búsquedas (?tab=)
    │       ├── Limpiar local · Refresh warehouse
    │       └── Sin paginación en listas largas
    │
    ├── ANÁLISIS
    │   ├── Análisis (/analytics)        [legacy package]
    │   ├── Tendencias (/trending)       [top 25 global]
    │   └── Comparativas (/comparatives) [heatmap géneros, sin paginar]
    │
    ├── RECOMENDACIONES
    │   └── Recomendaciones (/recommendations)
    │
    ├── DATOS (solo engineer/admin)
    │   ├── Pipeline ELT (/elt-pipeline)
    │   └── Explorador (/explorer)       [paginación 8/pág]
    │
    ├── SISTEMA
    │   └── Configuración (/settings)
    │
    ├── Huérfanos / acceso indirecto
    │   ├── Mi perfil (/users)           → menú usuario, NO sidebar
    │   └── 404 interno (/ruta-invalida) → not-found con link a /discover
    │
    ├── NO EXISTE
    │   └── Álbumes (/albums)            ❌ KPI visible, módulo ausente
    │
    └── Player (footer persistente)
        ├── Play/Pause · Prev/Next · Shuffle · Repeat
        ├── Progreso · Volumen · Cola
        ├── Favorito · Añadir a playlist
        └── Expandir → Now Playing View
```

---

## Auditoría de navegación (por pantalla)

| Pantalla | Ruta | ¿Desde dónde llega? | ¿Volver fácil? | Breadcrumb | Botón regresar | Pierde contexto | Callejón sin salida |
|----------|------|---------------------|----------------|------------|----------------|-----------------|---------------------|
| Inicio | `/discover` | Login, redirect `/`, 404 externo | N/A (home) | No | No | — | No |
| Centro analítico | `/dashboard` | Sidebar | Sidebar | No | No | Sí (sin origen) | No |
| Analítica streaming | `/insights/analytics` | Sidebar | Sidebar | No | No | Sí | No |
| Canciones destacadas | `/insights/tracks` | Sidebar | Sidebar | No | No | Sí | No |
| Artistas | `/artists` | Sidebar, Home | Sidebar | No | No | Parcial | No |
| Detalle artista | `/artists/:id` | Artistas, cards | Solo browser back | No | No | Sí | No |
| Canciones (catálogo) | `/tracks` | Sidebar, Home chips, detalle back | Sidebar | No | En detalle | Filtros URL entrantes ✓ | No |
| Detalle canción | `/tracks/:id` | Múltiples | Link fijo a catálogo | No | Sí (a `/tracks`) | Sí (no vuelve al origen) | No |
| Géneros | `/genres` | Sidebar, Home | Sidebar | No | No | — | No |
| Audio features | `/audio-features` | Sidebar | Sidebar | No | No | — | Parcial (6 tracks) |
| Buscar | `/search` | Sidebar, Home empty, History | Sidebar | No | No | Query `q` ✓ | No |
| Playlists | `/playlists` | Sidebar, Home | Sidebar | No | En detalle | — | No |
| Detalle playlist | `/playlists/:id` | Playlists, Home | Botón volver | No | Sí | — | No |
| Favoritos | `/liked` | Sidebar | Sidebar | No | No | — | No |
| Historial | `/history` | Sidebar, Home ×2 | Sidebar | No | No | Tab en URL ✓ | No |
| Análisis legacy | `/analytics` | Sidebar, Home "Ver más" | Sidebar | No | No | Confunde con `/dashboard` | No |
| Tendencias | `/trending` | Sidebar | Sidebar | No | No | Solapa con destacadas | No |
| Comparativas | `/comparatives` | Sidebar | Sidebar | No | No | — | No |
| Recomendaciones | `/recommendations` | Sidebar, Home | Sidebar | No | No | — | No |
| ELT Pipeline | `/elt-pipeline` | Sidebar (engineer) | Sidebar | No | No | — | No |
| Explorador | `/explorer` | Sidebar (engineer) | Sidebar | No | No | — | No |
| Configuración | `/settings` | Sidebar | Sidebar | No | No | — | No |
| Mi perfil | `/users` | Menú usuario | Menú | No | No | No en sidebar | No |
| Login | `/login` | Logout, guest guard | — | No | No | — | No |
| 404 | `/**` (hijo) | URL inválida | Link a Inicio | No | Sí | — | No |

**Hallazgo transversal 🟠 NAV-01:** No existe breadcrumb en ninguna pantalla. El usuario que llega desde Home → card → detalle no tiene indicación de ruta ni retorno contextual.

**Hallazgo transversal 🟠 NAV-02:** Mi perfil (`/users`) es accesible solo desde el menú de usuario; no aparece en sidebar. Funcional pero fácil de pasar por alto.

---

## Auditoría obligatoria: botones "Ver todo" / "Ver más"

| Ubicación | Texto | Destino actual | Destino esperado (PO) | Conserva contexto | Prioridad |
|-----------|-------|----------------|----------------------|-------------------|-----------|
| Home → Recientes | Ver todo | `/history` | Historial completo | No aplica | 🟢 OK |
| Home → Recomendado | Ver todo | `/recommendations` | Recomendaciones | No aplica | 🟢 OK |
| Home → Descubrir | Ver todo | `/tracks` | Rail ampliado o ranking discover | ❌ Abre catálogo CRUD sin filtro discover | 🟠 VT-01 |
| Home → Artistas | Ver todo | `/artists` | Listado artistas | No aplica | 🟢 OK |
| Home → Playlists | Ver todo | `/playlists` | Listado playlists | No aplica | 🟢 OK |
| Home → Géneros | Ver todo | `/genres` | Listado géneros | No aplica | 🟢 OK |
| Home → Actividad | Ver todo | `/history` | Historial | No aplica | 🟢 OK |
| Banda analítica | Ver más | `/analytics` | Panel enterprise coherente | ❌ Va a módulo legacy, no `/dashboard` | 🟠 VT-02 |
| Chips género (Home) | (chip click) | `/tracks?genre_id=` | Catálogo filtrado | ✓ Filtro en URL | 🟢 OK |
| Trending hero | Ver detalle | `/tracks/:id` | Detalle track | ✓ | 🟢 OK |

**Nota PO:** El usuario que pulsa "Ver todo" en **Descubrir** espera continuar el mismo tipo de contenido (exploración curada), no aterrizar en el administrador de catálogo con 50 filas paginadas.

---

## Paginación — matriz de estrategias

| Módulo | Estrategia | Tamaño página | ¿Carga nuevos datos? | Filtros al paginar | Consistencia |
|--------|-----------|---------------|----------------------|-------------------|--------------|
| Canciones `/tracks` | Paginación numérica | 50 | ✓ API | Búsqueda/filtro se mantienen | Patrón catálogo |
| Artistas `/artists` | Paginación numérica | 50 | ✓ API | Búsqueda se mantiene | Patrón catálogo |
| Géneros `/genres` | Paginación numérica | 50 | ✓ API | Búsqueda se mantiene | Patrón catálogo |
| Destacadas `/insights/tracks` | Infinite scroll | 20 | ✓ API (+ fallback client pool) | N/A | **Diferente** 🟡 |
| Buscar `/search` | Paginación tracks | 20 | ✓ API | Query en memoria | **Diferente** 🟡 |
| Explorador `/explorer` | Paginación | 8 | ✓ API | Por tabla | **Diferente** 🟡 |
| Detalle artista | "Cargar más" | batch | ✓ API | N/A | **Tercer patrón** 🟡 |
| Favoritos `/liked` | Ninguna | todos | Una carga | — | 🟡 PAG-01 |
| Historial `/history` | Ninguna | todos | Una carga | Tab en URL | 🟡 PAG-02 |
| Comparativas | Ninguna | todos géneros | Una carga | — | 🟡 |
| Recomendaciones | Ninguna aparente | rail | Una carga | — | 🟡 |
| Trending | Ninguna | top 25 | Una carga | — | OK para ranking |
| Perfil `/users` | Client-side slice | 8 | Memoria local | — | 🟡 |
| Dashboard `/dashboard` | Tabla widget | 8 | Client slice | — | 🟡 |

**Hallazgo 🟡 PAG-03:** No hay scroll restoration documentado; al paginar en catálogo el scroll de `.page-content` probablemente permanece abajo (comportamiento típico SPA sin reset).

**Hallazgo 🟡 PAG-04:** Tres patrones de listado largo (paginación clásica, infinite scroll, load more) sin guía visual común para el usuario.

---

## Búsquedas — matriz de verificación

| Módulo | Debounce | Case-insensitive | Vacío | Error API | Parcial | URL sync |
|--------|----------|------------------|-------|-----------|---------|----------|
| `/tracks` | 350ms ✓ | Servidor | Estado vacío ✓ | Mensaje i18n ✓ | — | Solo lectura query params |
| `/artists` | 350ms ✓ | Servidor | ✓ | ✓ | — | No |
| `/genres` | 350ms ✓ | Servidor | ✓ | ✓ | — | No |
| `/search` | 350ms ✓ | Servidor | ✓ | ✓ Parcial | ✓ | `?q=` lectura ✓ |
| Historial búsquedas | — | — | ✓ | Hub error | — | Tab `?tab=search` |

**Hallazgo 🟡 SRCH-01:** Filtros activos en `/tracks` no se escriben de vuelta a la URL al buscar o paginar; solo se leen al entrar (p. ej. desde chip de género en Home). Compartir URL pierde búsqueda de texto.

**Hallazgo 🟢 SRCH-02:** Historial de búsqueda enlaza correctamente a `/search?q=...`.

---

## Filtros

| Módulo | Combinables | Persisten | Limpiar | URL | Rompen paginación |
|--------|-------------|-----------|---------|-----|-------------------|
| Tracks catálogo | Género XOR artista | En sesión | ✓ chip | Entrada ✓ / salida ✗ | Reset a pág. 1 ✓ |
| Insights analytics | Rango fechas | En componente | ✓ | No | Refetch ✓ |
| Artists | Búsqueda | Sesión | ✓ | No | Reset pág. 1 ✓ |
| Genres | Búsqueda | Sesión | ✓ | No | Reset pág. 1 ✓ |

---

## Cards — comportamiento

| Tipo | Clickeable | Destino | Hover | Imagen/placeholder | Acciones inline |
|------|------------|---------|-------|-------------------|-----------------|
| `media-card` (Home, destacadas) | ✓ | `/tracks/:id` | Consistente | Cover + gradient fallback | Play overlay |
| Artist chip (Home) | ✓ | `/artists/:id` | ✓ | Avatar | — |
| Genre chip (Home) | ✓ | `/tracks?genre_id` | ✓ | Icon | — |
| KPI card (Home) | ✗ | — | Tooltip | — | No navega a módulo |
| KPI Álbumes | ✗ | **Sin `/albums`** | Tooltip | — | 🔴 CARD-01 |
| Track row | ✓ | Play + links | Consistente | — | Favorito |
| Playlist card | ✓ | `/playlists/:id` | ✓ | Gradient | — |
| Metric card (dashboard) | ✗ | — | — | — | Solo lectura |

**Hallazgo 🔴 CARD-01:** KPI "Álbumes" muestra `total_albumes` del warehouse pero no existe módulo navegable. El usuario no puede "ver todo" ni explorar álbumes.

---

## Player

| Criterio | Estado | Notas |
|----------|--------|-------|
| Persistente entre rutas | ✓ | E2E `player-bar` en todas las rutas |
| No desaparece | ✓ | Footer fijo en layout |
| Controles visibles | ✓ | Play disabled sin track |
| Responsive | Parcial 🟡 | Barra compacta; Now Playing expandible |
| No tapa contenido | ✓ | Layout reserva espacio |
| Comportamiento Spotify-like | Parcial 🟡 | Demo audio WAV local, no streaming real |
| Favorito / playlist desde player | ✓ | Integrado |
| Cola visible | ✓ | Pill con count |

**Hallazgo 🟡 PLAY-01:** Audio es demo (`/assets/audio/demo-*.wav`); correcto para demo pero debe etiquetarse claramente al usuario final.

---

## Historial

| Criterio | Estado | Notas |
|----------|--------|-------|
| Orden cronológico | ✓ | `viewed_at` / `fecha_evento` |
| Persistencia local | ✓ | `HistoryService` + PocketBase/API |
| Fecha/hora relativa | ✓ | `relativeTime()` en Home |
| Duplicados | Parcial | Home dedupe por título; historial completo puede repetir |
| Acceso rápido | ✓ | Home recientes + tab música |
| Paginación | ✗ 🟡 | Lista completa en DOM |
| Limpiar | ✓ | Por tab (música/búsquedas) |

---

## Favoritos

| Criterio | Estado | Notas |
|----------|--------|-------|
| Agregar / eliminar | ✓ | `FavoriteBtnComponent` + API |
| Persistencia | ✓ | `FavoritesService.refreshIds()` en layout init |
| Feedback visual | ✓ | Pop animation, aria-pressed |
| Iconos | ✓ | Corazón coherente |
| Sincronización | ✓ | Observable ids |
| Listado `/liked` | ✓ | Play all, estados vacío/error |
| Paginación | ✗ 🟡 | Todos en una vista |

---

## Playlists

| Criterio | Estado | Notas |
|----------|--------|-------|
| Crear | ✓ | Modal |
| Editar / eliminar | ✓ | Confirm dialog |
| Detalle por URL | ✓ | `/playlists/:id` |
| Agregar canción | ✓ | `AddToPlaylistBtn` |
| Eliminar canción | ✓ | En detalle |
| Portada | Gradient + optional cover track | 🟢 |
| Cantidad / duración | ✓ | Estimada si no hay durations |
| Orden | Lista API | Sin reorder drag 🟡 |

---

## Dashboard / KPIs

| Fuente | Módulo | ¿Datos reales? | Problema |
|--------|--------|----------------|----------|
| API summary | Home hero KPIs | ✓ warehouse | Trends **hardcoded** 🔴 |
| API summary | Home band KPIs | ✓ | Favoritos = Likes mismo valor 🔴 |
| `KPI_TRENDS` | home-metrics.util.ts | ❌ +6%, +8%… fijos | 🔴 KPI-01 |
| Enterprise API | `/dashboard` | ✓ DuckDB Gold | Error backend `skip_rate` puede vaciar cache 🔴 |
| Stats API | `/analytics` legacy | ✓ | Duplica propósito con `/dashboard` 🟠 |
| Stats API | `/insights/analytics` | ✓ | Tercer panel analítico 🟠 |
| Local estimations | Minutos hoy, racha | Parcial | `n * 3.5 min` estimado 🟡 |

**Hallazgo 🔴 KPI-01:** Constante `KPI_TRENDS` en `home-metrics.util.ts` inyecta porcentajes ficticios (+6%, +8%…) con badge "demo" fácil de ignorar. Viola requisito "no KPIs hardcodeados".

**Hallazgo 🔴 KPI-02:** Tarjetas "Favoritos" y "Likes" muestran el mismo `favoritesCount()` — redundancia confusa.

**Hallazgo 🟠 KPI-03:** Tres entradas de sidebar para analítica ("Centro analítico", "Analítica de streaming", "Análisis") sin jerarquía clara para el oyente.

---

## Menú lateral

| Criterio | Estado | Notas |
|----------|--------|-------|
| Orden lógico | Parcial 🟡 | Enterprise arriba, legacy "Análisis" abajo |
| Iconos | Parcial 🟠 | Mismo icono música en "Canciones" y "Canciones destacadas" |
| Jerarquía secciones | ✓ | 6 secciones etiquetadas |
| Responsive | ✓ | Overlay móvil + collapse desktop |
| Estado activo | ✓ | `routerLinkActive` |
| Rutas correctas | ✓ | Todas resuelven |
| Engineer-only | ✓ | Sección DATOS oculta para oyente |
| Cerrar sesión | ✓ | Menú usuario → `logout()` |

**Hallazgo 🟠 NAV-03:** Usuario oyente ve 3 módulos de ranking/análisis de canciones: Canciones destacadas, Canciones (catálogo), Tendencias — sin explicación de diferencia.

---

## Módulos — checklist funcional

Leyenda: ✓ cumple · ⚠️ parcial · ✗ ausente

| Módulo | Listado | Detalle | Búsqueda | Filtros | Orden | Paginación | Loading | Vacío | Error | Responsive |
|--------|---------|---------|----------|---------|-------|------------|---------|-------|-------|------------|
| Inicio | ✓ rails | vía cards | — | — | — | — | ✓ | ✓ | ✓ | ✓ |
| Dashboard enterprise | ✓ KPIs | — | — | — | — | tabla 8 | ✓ | ✓ | ✓ | ✓ |
| Insights analytics | ✓ charts | — | — | fechas | — | — | ✓ | ✓ | ✓ | ✓ |
| Destacadas | ✓ grid | ✓ card | ✗ | ✗ | ranking fijo | infinite | ✓ | ✓ | ✓ | ✓ |
| Artistas | ✓ | ✓ | ✓ | — | ✓ | ✓ 50 | ✓ | ✓ | ✓ | ✓ |
| Canciones | ✓ | ✓ | ✓ | ✓ | — | ✓ 50 | ✓ | ✓ | ✓ | ✓ |
| **Álbumes** | **✗** | **✗** | **✗** | **✗** | **✗** | **✗** | **—** | **—** | **—** | **—** |
| Géneros | ✓ | ✗ | ✓ | — | — | ✓ 50 | ✓ | ✓ | ✓ | ✓ |
| Audio features | ⚠️ 6 | ✓ selector | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| Buscar | ✓ | ✓ links | ✓ | — | — | ✓ 20 | ✓ | ✓ | ✓ | ✓ |
| Playlists | ✓ | ✓ | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| Favoritos | ✓ | vía row | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| Historial | ✓ tabs | ✓ links | — | tabs | cronológico | ✗ | ✓ | ✓ | ✓ | ✓ |
| Analytics legacy | ✓ KPIs | — | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| Trending | ✓ 25 | ✓ hero | ✗ | ✗ | ranking | ✗ | ✓ | ✓ | ✓ | ✓ |
| Comparativas | ✓ heatmap | — | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| Recomendaciones | ✓ | ✓ cards | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| ELT | ✓ pipeline | — | — | — | — | — | ✓ | ✓ | ✓ | ✓ |
| Explorer | ✓ tablas | preview | ✗ | tabla | — | ✓ 8 | ✓ | ✓ | ✓ | ✓ |
| Settings | ✓ tabs | — | — | — | — | — | ✓ | — | ✓ | ✓ |
| Users | ✓ perfil | — | ⚠️ history filter | — | — | client 8 | ✓ | ✓ | ✓ | ✓ |

---

## Estados (loading / error / vacío / sin conexión)

| Pantalla | Loading | Error | Vacío | Timeout explícito |
|----------|---------|-------|-------|-------------------|
| Mayoría módulos | ✓ skeleton/spinner | ✓ retry | ✓ CTA | ✗ mensaje genérico API |
| Dashboard enterprise | ✓ EmptyState | ✓ retry | ✓ no-data | ✗ |
| Home | ✓ defer placeholder | ✓ link catálogo | ✓ link buscar | ✗ |

**Hallazgo 🟡 STATE-01:** No hay patrón unificado "sin conexión" / offline; todos usan mensaje de error de backend.

---

## Coherencia visual y de producto

| Pregunta | Evaluación |
|----------|------------|
| ¿Misma identidad visual? | **Mayormente sí** — glass panels, verde `#1ed896`, dark theme |
| ¿Mismos componentes? | **Parcial** — Home usa `kpi-card`; Dashboard usa `metric-card`; Analytics legacy usa divs custom 🟡 |
| ¿Mismo lenguaje? | **Parcial** — `/insights/tracks` hardcoded ES; `/trending` mezcla ES hardcoded + i18n 🟠 |
| ¿Mismos patrones de acción? | **Parcial** — paginación inconsistente (ver matriz) |
| ¿Parece un solo producto? | **Casi** — capas enterprise vs legacy visibles en analítica |

**Hallazgo 🟠 COH-01:** Dos sistemas de analítica en paralelo (enterprise `/dashboard` + `/insights/*` vs package legacy `/analytics`, `/trending`, `/comparatives`) generan sensación de producto compuesto.

**Hallazgo 🟠 COH-02:** `/insights/tracks` titulado "Canciones destacadas" vs sidebar "Canciones" (`/tracks`) — homonimia casi segura de confusión.

---

## Registro de hallazgos (priorizado)

### 🔴 Críticos

| ID | Pantalla | Ruta | Componente | Impacto | Corrección propuesta |
|----|----------|------|------------|---------|----------------------|
| KPI-01 | Home | `/discover` | `home-metrics.util.ts` → `KPI_TRENDS` | Usuario ve tendencias falsas (+6%, etc.) | Calcular trend real desde warehouse o ocultar hasta tener dato |
| KPI-02 | Home | `/discover` | `home-analytics-band.component.html` | Favoritos = Likes duplicado | Eliminar una tarjeta o diferenciar métricas (likes vs favorites API) |
| CARD-01 | Home | `/discover` | KPI álbumes | Promete entidad sin módulo | Crear `/albums` o quitar KPI / enlazar a explorer `dim_album` |
| NAV-04 | Sidebar | — | `app.routes.ts` | **No existe `/albums`** en auditoría solicitada | Implementar módulo álbumes o remover del mapa mental/KPIs |
| COH-03 | Destacadas | `/insights/tracks` | `features/tracks/*` vs E2E | Tests esperan `table-widget`; UI es grid infinite scroll | Alinear tests con producto o documentar intención |
| KPI-04 | Dashboard | `/dashboard` | Backend DuckDB | Cache warm falla (`skip_rate` column) | Fix SQL schema; KPIs pueden estar vacíos/incorrectos |

### 🟠 Altos

| ID | Pantalla | Ruta | Componente | Impacto | Corrección propuesta |
|----|----------|------|------------|---------|----------------------|
| VT-01 | Home | `/discover` | `horizontal-section` link=`/tracks` | "Ver todo" Descubrir ≠ contenido del rail | Cambiar a vista discover dedicada o `/insights/tracks` si es ranking |
| VT-02 | Home | `/discover` | `home-analytics-band` | "Ver más" va a legacy `/analytics` | Enlazar a `/dashboard` o renombrar sección |
| NAV-01 | Global | — | layout | Sin breadcrumbs | Añadir `BreadcrumbComponent` con rutas semánticas |
| NAV-03 | Sidebar | — | `dashboard-layout` | 3 conceptos "canciones/analytics" | Renombrar, reagrupar o añadir descripciones |
| COH-01 | Analítica | múltiples | packages vs features | Usuario no sabe qué panel usar | Unificar bajo "Centro analítico" con sub-tabs |
| COH-02 | Tracks | `/tracks` vs `/insights/tracks` | nombres i18n | Confusión catálogo vs ranking | Renombrar nav: "Catálogo" vs "Top charts" |
| DET-01 | Detalle track | `/tracks/:id` | back link | Siempre vuelve a catálogo | `Location.back()` o breadcrumb contextual |
| I18N-01 | Destacadas / Trending | `/insights/tracks`, `/trending` | templates | ES hardcoded, producto bilingüe roto | Migrar strings a `es.ts` / `en.ts` |
| SRCH-01 | Catálogo | `/tracks` | `tracks.component.ts` | URL no refleja búsqueda activa | Sync bidireccional query params |

### 🟡 Medios

| ID | Pantalla | Ruta | Componente | Impacto | Corrección propuesta |
|----|----------|------|------------|---------|----------------------|
| PAG-01 | Favoritos | `/liked` | — | Listas largas sin paginar | Virtual scroll o paginación |
| PAG-02 | Historial | `/history` | — | Idem | Paginación o infinite scroll |
| PAG-03 | Catálogo | `/tracks`, `/artists` | — | Scroll no resetea al paginar | Scroll to top en cambio de página |
| PAG-04 | Global | — | — | 3 patrones de listado | Estandarizar guía UX en design system |
| PLAY-01 | Player | global | demo audio | Expectativa streaming real | Badge "Demo audio" visible |
| AF-01 | Audio features | `/audio-features` | carga 6 tracks | Módulo sidebar promete más | Listado completo + buscador |
| GEN-01 | Géneros | `/genres` | — | Sin página detalle género | Detalle con tracks filtrados |
| PL-01 | Playlists | detalle | — | Sin reordenar tracks | Drag & drop opcional |
| STATE-01 | Global | — | — | Sin estado offline | Detectar `navigator.onLine` |
| EST-01 | Home widgets | `/discover` | `listenMinutesToday` | Minutos estimados, no reales | Etiquetar "estimado" en UI (parcial en tips) |

### 🟢 Bajos / OK

| ID | Nota |
|----|------|
| OK-01 | Player persistente verificado E2E |
| OK-02 | Debounce 350ms consistente en catálogos |
| OK-03 | Estados vacío/error presentes en mayoría de módulos |
| OK-04 | Engineer guard oculta ELT/Explorer correctamente |
| OK-05 | Favoritos con feedback visual y persistencia |
| OK-06 | Historial tabs sincronizados con `?tab=` |
| OK-07 | Search recibe `?q=` desde historial |
| OK-08 | Sidebar collapse persiste en localStorage |
| OK-09 | Playlists CRUD completo funcional |
| OK-10 | 404 interno con escape a Inicio |

---

## Auditoría de botones (muestra representativa)

### Sidebar (17 ítems visibles oyente)

Todos: ✓ existen, ✓ visibles, ✓ rutas correctas, ✓ estado activo.  
**Excepción 🟠:** iconos duplicados música en Canciones / Canciones destacadas.

### Home

| Botón | ¿Promete? | ¿Cumple? |
|-------|-----------|----------|
| Play en tile reciente | Reproduce track | ✓ |
| Ver todo (×6) | Ver listado completo | ⚠️ Descubrir → catálogo (VT-01) |
| Ver más analítica | Más analítica | ⚠️ Legacy (VT-02) |
| Chip género | Tracks del género | ✓ |

### Catálogo Canciones (steward)

| Botón | ¿Cumple? |
|-------|----------|
| Crear / Editar / Eliminar | ✓ solo si `isCatalogSteward()` |
| Buscar / Limpiar | ✓ |
| Paginación | ✓ |
| Retry error | ✓ |

### Player

| Botón | Disabled | Loading | Feedback |
|-------|----------|---------|----------|
| Play | ✓ sin track | — | toggle icon |
| Prev/Next | — | — | ✓ |
| Shuffle/Repeat | — | — | active class |
| Favorito | — | — | pop animation |
| Seek bar | — | — | ✓ |

### Cerrar sesión

| Botón | Ubicación | Acción |
|-------|-----------|--------|
| Cerrar sesión | Menú usuario header | ✓ stop playback + `/login` |

**Hallazgo 🟢:** No se detectaron botones completamente desconectados (dead clicks) en revisión de código.

---

## Compartir

**Hallazgo 🟡 SHR-01:** No existe funcionalidad "Compartir" en cards de canción, detalle track ni playlists. El mapa de auditoría solicitado incluía Compartir bajo Canciones — **módulo no implementado**.

---

## Confusión Dashboard vs auditoría solicitada

El flujo solicitado menciona "Dashboard" como primer paso. En el producto:

- **Default post-login:** `/discover` (Inicio), no `/dashboard`.
- **"Centro analítico":** `/dashboard` (enterprise).
- **"Dashboard analítico" del enunciado** puede referirse a `/dashboard` o al bloque analítico en Home.

**Recomendación PO 🟡:** Clarificar en onboarding que "Inicio" es el hub de consumo y "Centro analítico" es el hub de métricas.

---

## Desalineación E2E vs producto actual

| Test | Expectativa | Realidad actual | Prioridad |
|------|-------------|-----------------|-----------|
| `analytics-modules.spec.ts` → insights/tracks | `table-widget`, botón recomendaciones | Grid `media-card`, infinite scroll, sin recomendaciones | 🔴 COH-03 |
| navigation.spec.ts | 19 rutas cargan h1 | ✓ estructura válida | 🟢 |

---

## Matriz de coherencia por pantalla

| Pantalla | ¿Mismo producto? | Identidad | Componentes | Lenguaje | Patrones |
|----------|------------------|-----------|-------------|----------|----------|
| Inicio | ✓ | ✓ | kpi-card | i18n ✓ | rails Spotify-like |
| Centro analítico | ✓ | ✓ | metric-card, chart-widget | ES hardcoded parcial | enterprise |
| Análisis legacy | ⚠️ | ✓ | custom kpi divs | i18n ✓ | distinto a enterprise |
| Catálogo | ✓ | ✓ | track-row, catalog CSS | i18n ✓ | CRUD modal |
| Destacadas | ✓ | ✓ | media-card | **ES hardcoded** | infinite scroll |
| Trending | ✓ | ✓ | custom | **mix ES/i18n** | hero + grid |

---

## Resumen ejecutivo PO

### Lo que funciona bien
- Arquitectura de layout con **player persistente** y sidebar completo.
- Catálogo (artistas, canciones, géneros) con **búsqueda debounced**, paginación server-side y estados vacío/error.
- Home rico en contenido con carriles horizontales estilo streaming.
- Separación clara de roles (oyente vs ingeniero).
- Playlists y favoritos con flujos completos.

### Lo que hace preguntar "¿y ahora qué?"
1. **Álbumes visibles en KPIs pero sin módulo** — promesa rota.
2. **Tres paneles de analítica + dos listados de canciones** — sobrecarga cognitiva.
3. **"Ver todo" de Descubrir** lleva a otro universo (catálogo admin).
4. **Tendencias KPI demo** (+6%, +8%) mezcladas con datos reales — credibilidad dañada.
5. **Sin breadcrumbs ni vuelta contextual** en detalles.

### Prioridad de fase 2 (cuando se autorice implementación)

1. 🔴 KPIs honestos (eliminar hardcode, deduplicar favoritos/likes).
2. 🔴 Decisión álbumes: módulo o eliminar KPI.
3. 🟠 Unificar narrativa analítica (1 hub, sub-rutas).
4. 🟠 Corregir destinos "Ver todo" / "Ver más".
5. 🟠 Breadcrumbs + i18n destacadas/trending.
6. 🟡 Estandarizar paginación y scroll restoration.

---

## Anexo: archivos clave revisados

| Área | Archivos |
|------|----------|
| Rutas | `apps/frontend/src/app/app.routes.ts` |
| Sidebar | `apps/frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts` |
| Home | `apps/frontend/src/app/packages/streaming/home/home.component.html` |
| Ver todo | `apps/frontend/src/app/shared/components/horizontal-section/horizontal-section.component.ts` |
| KPIs demo | `apps/frontend/src/app/packages/streaming/home/home-metrics.util.ts` |
| Destacadas | `apps/frontend/src/app/features/tracks/tracks.component.ts` |
| Catálogo | `apps/frontend/src/app/packages/streaming/tracks/tracks.component.ts` |
| Player | `apps/frontend/src/app/shared/components/player-bar/player-bar.component.html` |
| E2E | `automation/e2e/tests/navigation.spec.ts`, `analytics-modules.spec.ts` |

---

*Documento generado en Fase 1. Sin cambios de código. Listo para revisión PO y planificación de Fase 2.*
