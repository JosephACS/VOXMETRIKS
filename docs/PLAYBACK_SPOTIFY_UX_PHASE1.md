# PLAYBACK_SPOTIFY_UX — Fase 1

**Fecha:** 2026-07-05  
**Alcance:** UX Spotify Core — favoritos globales, cola global, acciones de track, estado reactivo  
**Backend:** Sin cambios

---

## Qué se implementó

### 1. Estado global consolidado

- **`PlaybackStore`** — lectura reactiva (signals) de transporte, cola, volumen, repeat/shuffle, autoplay, portada.
- **`PlayerController`** — facade única para intents (play, pause, queue, next, etc.) + expone `playback` store.
- **`FavoritesStore`** — ya existía; sigue siendo SSoT de favoritos vía `toSignal(favoriteIds$)`.
- **`QueueManager`** — cola global in-memory (sin cambios de lógica; ya integrada en `MusicPlayerService`).

La UI principal del reproductor (`PlayerBar`, `NowPlayingView`, `TrackRow`, `MediaCard`, `TrackContextMenu`) ahora lee **`PlaybackStore`** y actúa vía **`PlayerController`**.

### 2. `TrackActionsComponent` (nuevo)

Componente reutilizable que agrupa:

- `FavoriteBtnComponent`
- `TrackContextMenuComponent` (play now, play next, add to queue, add to playlist, ver artista, ver detalle)

Usado en: TrackRow, MediaCard, Search, History, Home (continue tiles), Trending.

### 3. `track.adapter.ts` (nuevo)

Fábrica canónica de `PlayableTrack` desde:

- `HistoryEntry`
- `TrackSearchResult`
- `FavoriteTrack`
- `Track` / `TopTrack` (delegación a factory existente)

### 4. Favoritos desde cualquier superficie

| Superficie | Antes | Después |
|------------|-------|---------|
| Tracks (TrackRow) | ✔ | ✔ TrackActions |
| Search | ✔ solo favorito | ✔ play + TrackActions |
| Recommendations (MediaCard) | ✔ duplicado | ✔ solo MediaCard (sin btn extra) |
| Artist detail (TrackRow) | ✔ | ✔ |
| Playlist detail (TrackRow) | ✔ | ✔ |
| Liked (TrackRow) | ✔ | ✔ + reactivo a FavoritesStore |
| History | ✗ | ✔ TrackActions |
| Home continue tiles | ✗ | ✔ TrackActions |
| Trending | ✔ solo favorito | ✔ TrackActions |
| Dashboard / Insights tracks (MediaCard) | ✔ | ✔ |

Actualización sin refresh: `FavoritesService` → optimistic `BehaviorSubject` → `FavoritesStore.favoriteIds` signal → todos los `FavoriteBtn` reaccionan. Home actualiza contador vía `favoriteIds$`.

### 5. Cola global

- Una sola cola en `QueueManager` (root singleton).
- Acciones: play now, play next, add to queue, next/previous, clear pending, remove (NowPlayingView).
- Search y History pasan `contextQueue` al reproducir.
- Persistencia session: track + cola + índice + history stack (ya existía).

### 6. Search — play inline

- Botón play directo en resultados.
- Ya no requiere navegar a `/tracks/:id` para reproducir.

---

## Arquitectura final (Fase 1)

```
UI (TrackActions, PlayerBar, páginas)
        │
        ├─ lectura ──► PlaybackStore (signals)
        │
        └─ intents ──► PlayerController
                              │
                              ▼
                     MusicPlayerService (orquestador legacy)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        QueueManager   PlaybackEngine   PlayerSourceResolver
              │                               │
              ▼                               ▼
        sessionStorage                   Backend audio-source

FavoritesStore ◄── FavoritesService ◄── HTTP /api/v1/favorites
     │
     └── FavoriteBtn (en TrackActions y PlayerBar)
```

---

## Archivos creados

| Archivo |
|---------|
| `apps/frontend/src/app/shared/components/track-actions/track-actions.component.ts` |
| `apps/frontend/src/app/playback-core/adapters/track.adapter.ts` |
| `apps/frontend/src/app/playback-core/playback-spotify-ux.phase1.spec.ts` |
| `docs/PLAYBACK_SPOTIFY_UX_PHASE1.md` |

## Archivos modificados (principales)

| Archivo | Cambio |
|---------|--------|
| `playback-core/playback.store.ts` | Store completo + helpers |
| `playback-core/player.controller.ts` | Facade con `playback` + métodos extendidos |
| `shared/components/track-row/*` | PlaybackStore + TrackActions |
| `shared/components/media-card/*` | PlayerController + TrackActions |
| `shared/components/track-context-menu/*` | PlayerController |
| `shared/components/player-bar/*` | PlaybackStore + PlayerController |
| `shared/components/now-playing-view/*` | PlaybackStore + PlayerController |
| `packages/streaming/search/*` | Play inline + TrackActions |
| `packages/history/*` | TrackActions + adapter |
| `packages/streaming/home/*` | TrackActions en continue tiles |
| `packages/analytics/trending/*` | TrackActions |
| `packages/streaming/liked/*` | PlayerController + adapter |
| `packages/streaming/playlists/*` | PlayerController |
| `packages/recommendations/recommendations.component.html` | Eliminar FavoriteBtn duplicado |

---

## Cómo funciona el estado global

1. **Mutación:** UI llama `PlayerController.playTrack()` / `addToQueue()` / etc.
2. **Orquestación:** `MusicPlayerService` actualiza `QueueManager` + signals internos.
3. **Lectura:** `PlaybackStore` expone los mismos signals — componentes usan `playback.currentTrack()`, `playback.queue()`, etc.
4. **Favoritos:** `FavoritesStore.toggle()` → HTTP → `favoriteIds$` → signal → UI reactiva en todas las cards.

---

## Cómo se actualizan favoritos sin refrescar

```typescript
FavoritesService.add/remove → BehaviorSubject<Set<number>> actualizado optimistamente
        ↓
FavoritesStore.favoriteIds (toSignal)
        ↓
FavoriteBtnComponent.active = computed(() => favoriteIds().has(trackId))
```

`LikedComponent` escucha cambios en `favoriteIds` y re-fetch lista automáticamente.

---

## Cómo funciona la cola

- **Origen:** `setQueue`, `playTrack` con context, `playNextInQueue`, `addToQueue`, autoplay append.
- **Global:** `QueueManager` en root injector — una instancia para toda la app.
- **UI cola:** `NowPlayingView` sidebar; pill count en `PlayerBar`.
- **Persistencia:** `sessionStorage` vía `player-session.storage.ts`.

---

## Pruebas ejecutadas

| Comando | Resultado |
|---------|-----------|
| `npm run build` | ✅ OK (warnings de budget preexistentes) |
| `npm run test` | ✅ 31/31 tests passed |
| `npm run lint` | ⚠️ 1 error preexistente en `features/tracks/tracks.component.ts` (no introducido por Fase 1) |
| Playwright | No configurado en este proyecto |
| pytest | No aplicable (sin cambios backend) |

### Tests nuevos (`playback-spotify-ux.phase1.spec.ts`)

1. Agregar favorito sin reproducir
2. Toggle favorito delega a FavoritesService
3. Agregar a cola sin reproducir
4. Play inmediato desde card
5. Play next sin reemplazar track actual
6. Cola global persiste en store entre calls
7. Store expone estado para player persistente

---

## Pendientes Fase 2+

- Migrar páginas restantes que aún inyectan `MusicPlayerService` directamente (artist-detail, tracks pages, track-detail, dashboard-layout logout).
- `PlayerTransportControlsComponent` compartido (eliminar duplicación PlayerBar/NowPlaying).
- Drag reorder en cola UI (`moveInQueue` API ya existe).
- Conectar `/api/v2/stream/*` analytics.
- Extraer providers de audio (YouTube/HTML5) — **fuera de alcance Fase 1**.
- Eliminar `MusicPlayerService` como god service (delegación completa al Controller).

---

*Fase 1 completada — reproducción actual intacta, build y tests OK.*
