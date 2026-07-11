# AUDIT_PLAYBACK_CORE — VOXMETRIKS

**Fecha:** 2026-07-05  
**Alcance:** Frontend (Angular 17+) + Backend (FastAPI) — sistema de reproducción completo  
**Objetivo:** Documentar el estado real antes de diseñar Playback Core V2  
**Estado:** Solo auditoría — sin cambios de código de producción

---

## 1. Resumen ejecutivo

VOXMETRIKS tiene un **reproductor global funcional** montado en `DashboardLayoutComponent` (`PlayerBar` + `NowPlayingView`). La reproducción es **YouTube-first** (IFrame API) con fallback a **8 WAV demo** locales. No existen servicios llamados `AudioService`, `PlaybackService` ni `TrackService`; el equivalente es **`MusicPlayerService`**.

Existe una **migración parcial iniciada** en `apps/frontend/src/app/playback-core/` (`QueueManager`, `PlaybackEngine`, `PlayerController`, `PlaybackStore`, `FavoritesStore`), pero **ningún componente de UI la consume todavía**. Toda la app sigue inyectando `MusicPlayerService` directamente.

**No hay un único Source of Truth formal.** Convergencia práctica en `MusicPlayerService` + `QueueManager` para transporte/cola, pero coexisten estados paralelos en favoritos, historial UX, listen-stats, colas locales por página y fábricas duplicadas de `PlayableTrack`.

**Gap crítico:** El backend expone analytics en `/api/v2/stream/*` pero el **frontend no lo consume**. Las reproducciones reales no alimentan `fact_streaming`.

**No existe `MiniPlayer`** como componente separado. `PlayerBarComponent` cumple ese rol.

---

## 2. Cómo se reproduce una canción

### Flujo end-to-end

```
UI (TrackRow / MediaCard / página / TrackContextMenu)
  → construye PlayableTrack (+ queue opcional)
  → MusicPlayerService.playTrack() | setQueue() | playNow()
  → QueueManager → PlayerQueue (in-memory)
  → loadTrack()
      → QueueManager.recordPlayed() (track anterior → PlaybackHistoryStack)
      → HistoryService.add() (localStorage UX)
      → TrackCoverService.cover$()
      → PlayerSourceResolver.resolve()
          → GET /api/v1/tracks/{id}/audio-source
          → YouTube (YoutubeEngineService) | demo WAV (HTMLAudioElement)
  → PlayerPlaybackEngine (tick 250ms → ListenStatsService)
  → Signals → PlayerBar / NowPlayingView
```

### Puntos de entrada UI

| Origen | Método | Cola |
|--------|--------|------|
| `track-row.component.ts` | `playTrack` | `[queue]` input |
| `media-card.component.ts` | `playTrack` | `[queue]` input |
| `track-context-menu.component.ts` | `playNow` / `playNextInQueue` / `addToQueue` | context queue |
| `home.component.ts` | `playTrack(historyPlayable(h))` | **sin cola** (single) |
| `liked.component.ts` | `setQueue` | `likedQueue` |
| `playlists.component.ts` | `setQueue` / TrackRow | `playlistQueue` |
| `artist-detail`, `tracks`, `recommendations`, `trending`, `history`, `track-detail`, `now-playing-view` | varios | cola local por página |
| `search.component.ts` | **no reproduce** | navega a `/tracks/:id` |
| `features/tracks/tracks.component.ts` | TrackRow | `trackQueue` |

### Comportamiento single-track

Si `playTrack(track)` se llama **sin** cola que contenga el track, `QueueManager.setSingle(track)` **reemplaza toda la cola** por un solo ítem. Se pierde el contexto previo.

Si el track ya está en la cola global con más de un ítem, `jumpTo(index)` y reproduce sin reemplazar.

---

## 3. Obtención de URL / fuente de audio

### Frontend

1. Al crear `PlayableTrack`, siempre se asigna `audioUrl = demoAudioUrlForTrack(id)` (`shared/config/demo-audio.config.ts`).
2. En `loadTrack`, `PlayerSourceResolver`:
   - Si `track.youtubeVideoId` ya existe → YouTube directo.
   - Si no → `TracksService.getAudioSource(id)`.
   - `status: pending` → poll hasta 8 intentos (800ms–2500ms backoff).
   - `status: ok` + `youtube_video_id` → actualiza track en memoria y YouTube.
   - 404 → elimina de `HistoryService` local, demo fallback.
   - `not_found` / error → demo fallback.
3. Error YouTube en reproducción → `recoverFromYoutubeError` con `force=true` **una vez**; luego demo.
4. Error demo → mensaje UI + auto-`next()` si hay más cola o autoplay (1.2s delay).

### Backend (`audio_source_service.py`)

| Paso | Detalle |
|------|---------|
| Query | `"{track_name} {artist_name} official audio"` |
| Resolver primario | yt-dlp `ytsearch12:` |
| Fallback | YouTube Data API v3 (`YOUTUBE_API_KEY`) |
| Scoring | Duración, títulos oficiales; rechaza covers/live/lyrics/loops |
| Cache | DuckDB `app_track_audio_source` (PK `track_id`) |
| Async default | `async_resolve=true` → thread daemon + respuesta `pending` |
| Estados | `ok`, `not_found`, `pending`, `error` (error **no** se cachea) |

**No hay proxy de bytes de audio.** El backend resuelve `youtube_video_id`; el cliente reproduce vía IFrame oculto 1×1.

---

## 4. Cola (Queue)

### Dónde vive

| Capa | Ubicación | Persistencia |
|------|-----------|--------------|
| Lógica autoritativa | `QueueManager` → `PlayerQueue` | No (memoria) |
| Espejo UI | `MusicPlayerService.queue`, `queueIndex` signals | No |
| Historial Previous | `PlaybackHistoryStack` en QueueManager | sessionStorage vía persist |
| Por página | `trackQueue`, `likedQueue`, `playlistQueue`, etc. | No |

### Cómo nace

- `setQueue(tracks, startIndex)` — playlist, liked play-all, artist play-all.
- `playTrack(track, queue)` — si `queue` contiene el track, usa índice; si no, cola de 1.
- `playNextInQueue(track)` — inserta después del actual (`insertNext`).
- `addToQueue(track)` — append único al final.
- Autoplay — `appendUnique` vía catálogo paginado o top tracks fallback.

### Cómo cambia

- `next()` / `previous()` / `onEnded()` → `QueueManager.advance` + `PlaybackHistoryStack`.
- **Shuffle:** índice aleatorio en `nextIndex()` (excluye actual cuando posible).
- **Repeat:** modos `off | all | one` via `cycleRepeatMode()` — **ya implementado**.
- **Autoplay al final:** fetch candidatos + `advanceWrapping` (repeat mode forzado a `all`).

### UI de cola

| Capacidad | API | UI |
|-----------|-----|-----|
| Ver cola | `player.queue()` | NowPlayingView sidebar |
| Click para saltar | `playFromQueue` | ✔ |
| Eliminar ítem | `removeFromQueue` | ✔ (NowPlayingView, no en track actual) |
| Limpiar pendientes | `clearPendingQueue` | ✔ |
| Reordenar drag | `moveInQueue` | **✗ API existe, sin UI** |
| Play next / add queue | `playNextInQueue` / `addToQueue` | TrackContextMenu (TrackRow, MediaCard) |

### Al cambiar de módulo

La cola **persiste en memoria** (singleton root). No se pierde al navegar rutas Angular.

**Persistencia en refresh:** `sessionStorage` guarda track, cola completa, índice, posición y `playbackHistory` (`player-session.storage.ts`). Restaura en **paused**; YouTube requiere user gesture para play.

### ¿Cola global real?

**Sí** — una instancia `QueueManager` en root injector. Es global y compartida entre todos los módulos.

---

## 5. Favoritos

### Cadena de datos

```
FavoritesService (HTTP + BehaviorSubject<Set<number>>)
        ↓ toSignal
FavoritesStore (playback-core/favorites.store.ts)
        ↓
FavoriteBtnComponent
```

### Dónde se puede agregar/quitar

| Superficie | FavoriteBtn |
|------------|-------------|
| TrackRow (listas) | ✔ |
| MediaCard | ✔ |
| PlayerBar | ✔ |
| NowPlayingView | ✔ |
| Track detail | ✔ |
| Search results | ✔ |
| Trending (hero + filas) | ✔ |
| Recommendations | ✔ |
| Home continue tiles | **✗** |
| Artist detail | vía TrackRow ✔ |

### Actualización UI

Optimistic vía `favoriteIds$` → signal. **No requiere refresh de página.** Desacoplado del player — favoritar no afecta cola ni reproducción.

`DashboardLayoutComponent.ngOnInit()` llama `favorites.refreshIds()` al bootstrap.

### Duplicación

Un solo componente `FavoriteBtnComponent` + un servicio HTTP. **Sin duplicación de lógica HTTP.**

---

## 6. Playlists

### Backend

CRUD `/api/v1/playlists` + add/remove track. Tablas `app_playlist`, `app_playlist_track`. **Sin endpoint reorder.**

### Frontend

| Acción | Estado |
|--------|--------|
| Crear / editar / borrar playlist | ✔ |
| Añadir track (`AddToPlaylistBtn`) | ✔ PlayerBar, NowPlaying, TrackDetail, TrackContextMenu |
| Quitar track | ✔ playlists detail |
| Reordenar (drag) | ✗ |
| Play playlist | ✔ `setQueue` |
| Play track en contexto | ✔ TrackRow + queue |

### Sincronización UI

Tras mutación, `playlists.component` re-fetch detail. **No hay estado global de playlists** — cada vista carga su propia lista. `NowPlayingView` muestra playlists recientes (solo links).

### Gap

`playlistQueue()` construye `PlayableTrack` inline con demo URL hardcoded — **no usa** `player-track.factory.ts`.

---

## 7. Reproductor inferior (PlayerBar)

**Ruta:** `shared/components/player-bar/`  
**Rol:** Bottom bar fijo (equivalente Spotify mini player).

| Control | Estado |
|---------|--------|
| Play/Pause | ✔ |
| Next/Previous | ✔ |
| Seek bar | ✔ `seekPct` |
| Volume + mute | ✔ persist localStorage |
| Shuffle | ✔ toggle |
| Repeat | ✔ cycle `off → all → one → off` |
| Expand | ✔ → NowPlayingView |
| Cover + metadata | ✔ |
| Favorite + Add to playlist | ✔ track actual |
| Queue pill/count | ✔ abre expanded view |
| Autoplay toggle | **✗** (solo en NowPlayingView hint) |

**NowPlayingView** duplica controles de transporte + sidebar cola editable (remove) + recomendadas + historial reciente.

---

## 8. Sincronización entre módulos

| Módulo | Acoplamiento |
|--------|--------------|
| `DashboardLayoutComponent` | Monta PlayerBar + NowPlayingView; `stopPlayback()` en logout; hydrate favorites/history |
| Páginas streaming/analytics | Inyectan `MusicPlayerService`, pasan colas locales computed |
| `HistoryService` | Escritura automática en cada `loadTrack()` |
| `ListenStatsService` | Tick cada ~250ms si `isPlaying` (localStorage por usuario) |
| `FavoritesStore` | Global, reactivo, independiente del player |
| Stream analytics v2 | **No conectado** |

### Mecanismos de sync

- **Angular signals** (`MusicPlayerService`) — transporte, cola espejo, UI player.
- **RxJS** — `FavoritesService.favoriteIds$`, `HistoryService.history$`, HTTP streams.
- **BehaviorSubject deprecated** — `MusicPlayerService.state$` (`{ playing: boolean }`).
- **EventEmitter** — no usado a nivel global de playback.
- **No NgRx / Akita** — estado local en servicios singleton.

---

## 9. Estado global — Source of Truth

| Dominio | Source of Truth | ¿Único? |
|---------|-----------------|---------|
| Track actual, playing, time, volume | `MusicPlayerService` signals | ✔ transporte |
| Cola activa | `QueueManager` → espejo en signals | ✔ (con espejo redundante) |
| Previous stack | `PlaybackHistoryStack` | ✔ |
| Favoritos IDs | `FavoritesService` → `FavoritesStore` | ✔ |
| Historial UX reciente | `HistoryService` (localStorage) | Paralelo — escrito en cada play |
| Minutos escuchados | `ListenStatsService` (localStorage) | Paralelo |
| Portadas player | `currentCover` signal | ✔ |
| Portadas listas | Por componente (cache local) | ✗ |
| Playlists usuario | HTTP + signals locales por vista | ✗ |
| Audio source cache | Backend DuckDB + `youtubeVideoId` en memoria | Híbrido |
| Facades no adoptados | `PlayerController`, `PlaybackStore` | **Huérfanos** |

**Conclusión:** No hay **Playback Store** unificado adoptado por la UI. `MusicPlayerService` sigue siendo un **god service** que orquesta transporte, cola, resolver, autoplay, persistencia y cover.

---

## 10. Componentes participantes

### UI playback

| Componente | Rol |
|------------|-----|
| `PlayerBarComponent` | Mini player bottom bar |
| `NowPlayingViewComponent` | Full-screen expanded player + cola |
| `TrackRowComponent` | Fila lista con play, favorite, context menu |
| `MediaCardComponent` | Card con play overlay, favorite, context menu |
| `TrackContextMenuComponent` | Play now / next / add queue / playlist |
| `FavoriteBtnComponent` | Toggle favorito |
| `AddToPlaylistBtnComponent` | Dropdown add to playlist |
| `DashboardLayoutComponent` | Shell global |

### Servicios / engines

| Servicio | Rol |
|----------|-----|
| `MusicPlayerService` | Orquestador principal (god service) |
| `QueueManager` | Cola + history stack (playback-core) |
| `PlayerQueue` | Lógica pura in-memory |
| `PlaybackEngine` | Wrapper injectable sobre `PlayerPlaybackEngine` |
| `PlayerPlaybackEngine` | HTML5 Audio + YouTube coordination |
| `YoutubeEngineService` | YouTube IFrame Player API |
| `PlayerSourceResolver` | Resolución YouTube vs demo |
| `player-track.factory.ts` | `playableFromTrack`, `playableFromTopTrack` |
| `player-session.storage.ts` | localStorage prefs + sessionStorage session |
| `TracksService` | Catalog + `getAudioSource()` |
| `TrackCoverService` / `CoverArtService` | Portadas |
| `HistoryService` | Historial UX localStorage |
| `ListenStatsService` | Segundos escuchados hoy |
| `FavoritesService` / `FavoritesStore` | Favoritos |
| `PlaylistsService` | CRUD playlists HTTP |

### Facades playback-core (no adoptados por UI)

| Clase | Estado |
|-------|--------|
| `PlayerController` | Delega 100% a MusicPlayerService — **0 consumidores UI** |
| `PlaybackStore` | Read-only facade — **0 consumidores UI** |

### Modelos

| Modelo | Ubicación |
|--------|-----------|
| `PlayableTrack`, `PlaybackStatus`, `RepeatMode` | `shared/models/player.models.ts` |
| `PlaybackPrefs`, `PersistedPlaybackSession` | `player-session.storage.ts` |
| `Track`, `TopTrack`, `FavoriteTrack`, `PlaylistDetail`, `AudioSource` | `shared/models/api.models.ts` |
| `PlayerState` | Legacy interface — no alineada con signals |

---

## 11. Endpoints participantes

| Endpoint | Uso actual frontend |
|----------|---------------------|
| `GET /api/v1/tracks/{id}/audio-source` | Resolución YouTube |
| `GET /api/v1/tracks`, `/search` | Autoplay fill |
| `GET /api/v1/tracks/top` (stats) | Autoplay fallback, NowPlaying recommendations |
| `GET/POST/DELETE /api/v1/favorites` | Favoritos |
| CRUD `/api/v1/playlists` | Playlists |
| `GET /api/v1/tracks/{id}/cover` | Portadas |
| `POST /api/v2/stream/start\|end\|skip\|pause\|resume` | **No usado** |

---

## 12. Capacidades de reproducción

| Feature | Estado |
|---------|--------|
| Play | ✔ |
| Pause | ✔ |
| Resume | ✔ (re-load si engine desincronizado) |
| Seek | ✔ |
| Next | ✔ |
| Previous | ✔ (seek 0 si >3s; else PlaybackHistoryStack) |
| Repeat off/all/one | ✔ |
| Shuffle | ✔ random index |
| Autoplay | ✔ append catálogo al final |
| Persist prefs (volume, shuffle, repeat, autoplay) | ✔ localStorage |
| Persist session (track, queue, position, history) | ✔ sessionStorage |
| Play next / add to queue | ✔ API + TrackContextMenu |
| Queue remove | ✔ NowPlayingView |
| Queue reorder drag | ✗ |
| Crossfade | ✗ |
| Lyrics | ✗ |
| Offline / cache | ✗ |
| Stream analytics | ✗ frontend disconnected |

---

## 13. Problemas de arquitectura

### Críticos

1. **God service:** `MusicPlayerService` mezcla cola, engine, resolver, autoplay, UI state, persistencia, cover.
2. **Facades huérfanos:** `PlayerController` + `PlaybackStore` creados pero UI no migrada — doble capa sin beneficio.
3. **PlayableTrack factories duplicadas** en ≥8 lugares con lógica demo URL inconsistente.
4. **Stream analytics desconectado** — warehouse no refleja reproducciones reales.
5. **Dual audio engines** (YouTube iframe + HTMLAudio) acoplados — difícil extender providers.

### Altos

6. PlayerBar y NowPlayingView **duplican template de controles** + `repeatTitle()` + `onProgressClick()`.
7. `moveInQueue` API sin UI — reorder incompleto vs Spotify.
8. Search sin play inline — UX inconsistente (solo navegación).
9. `state$` BehaviorSubject deprecated sin consumidores claros.
10. Colas locales por página reconstruyen `PlayableTrack` en cada computed — acoplamiento y duplicación.

### Medios

11. Cover fetching duplicado en TrackRow, MediaCard, NowPlayingView.
12. `trackQueue()` computed copy-paste en 6+ componentes.
13. Autoplay toggle no expuesto en PlayerBar.
14. Playlist sin reorder API ni UI.
15. `HistoryService` mezclado como side-effect obligatorio en cada play.

### Bajos

16. Dos páginas de tracks (`/tracks` vs `/insights/tracks`) con integraciones similares.
17. Negative track IDs → demo URL puede diferir según factory usada.

---

## 14. Responsabilidades mezcladas

| Clase | Mezcla |
|-------|--------|
| `MusicPlayerService` | Transport + queue + source + autoplay + persistence + cover + expanded UI state |
| `PlayerSourceResolver` | OK separado pero instanciado con `new` dentro del service |
| `HistoryService` | Historial UX + side effect obligatorio en cada play |
| `ListenStatsService` | Métricas UX + tick acoplado al engine |
| `NowPlayingViewComponent` | UI + fetch playlists + recommendations + cover cache local |

---

## 15. Código duplicado (inventario)

| Patrón | Ubicaciones |
|--------|-------------|
| `PlayableTrack` builders | `player-track.factory`, `home.historyPlayable`, `history.playFromHistory`, `now-playing.playHistoryEntry`, `track-detail.playTrack`, `liked.likedQueue`, `playlists.playlistQueue`, `recommendations.toPlayable` |
| Demo URL | `demoAudioUrlForTrack()` vs inline `` `/assets/audio/demo-${(id % 8) + 1}.wav` `` |
| Transport UI | `player-bar.html`, `now-playing-view.html` |
| `repeatTitle(mode)` | `PlayerBarComponent`, `NowPlayingViewComponent` |
| `onProgressClick` | `PlayerBarComponent`, `NowPlayingViewComponent` |
| Cover lazy load | `track-row`, `media-card`, `now-playing-view` |
| `trackQueue` computed | tracks, artist-detail, trending, recommendations, features/tracks |

---

## 16. Diagrama de arquitectura actual

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  PlayerBar │ NowPlaying │ TrackRow │ MediaCard │ Pages...   │
│  (todos inyectan MusicPlayerService directamente)            │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              MusicPlayerService (GOD SERVICE)                  │
│  signals: track, playing, queue, shuffle, repeatMode, etc.   │
│  + QueueManager + PlaybackEngine + SourceResolver + Autoplay   │
└─────┬──────────────┬──────────────┬──────────────────────────┘
      │              │              │
      ▼              ▼              ▼
 QueueManager    PlayerPlayback   History / ListenStats
 (PlayerQueue +  Engine + YT      (localStorage, parallel)
  HistoryStack)   + HTMLAudio
      │              │
      │              ▼
      │         PlayerSourceResolver → TracksService
      │              │
      ▼              ▼
 sessionStorage   Backend GET /tracks/{id}/audio-source
 (queue+history)  (yt-dlp → DuckDB cache → YouTube IFrame)

┌─────────────────────────────────────────────────────────────┐
│  playback-core/ (PARCIAL — NO ADOPTADO POR UI)               │
│  PlayerController ──delegates──► MusicPlayerService          │
│  PlaybackStore ──reads──► MusicPlayerService + QueueManager  │
│  FavoritesStore ──wraps──► FavoritesService ✔ (FavoriteBtn)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 17. Migración parcial existente (playback-core)

| Archivo | Estado | Adoptado |
|---------|--------|----------|
| `queue.manager.ts` | Completo | ✔ por MusicPlayerService |
| `playback-history.ts` | Completo (repeat/shuffle pure fn) | ✔ |
| `playback.engine.ts` | Wrapper injectable | ✔ por MusicPlayerService |
| `player.controller.ts` | Facade thin | ✗ UI |
| `playback.store.ts` | Read-only facade | ✗ UI |
| `favorites.store.ts` | Signal wrapper | ✔ FavoriteBtn |
| `queue.logic.ts` | Re-export de playback-history | Redundante |
| Tests | `player-queue.spec.ts`, `playback-history.spec.ts` | Parcial |

---

*Fin de auditoría — no se modificó código de producción.*
