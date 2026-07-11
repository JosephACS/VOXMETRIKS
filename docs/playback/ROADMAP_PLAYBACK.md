# ROADMAP_PLAYBACK — Implementación por fases

**Fecha:** 2026-07-05  
**Prerequisitos:** [AUDIT_PLAYBACK_CORE.md](./AUDIT_PLAYBACK_CORE.md), [PLAYBACK_ARCHITECTURE_V2.md](./PLAYBACK_ARCHITECTURE_V2.md)  
**Regla:** Una fase estable antes de la siguiente. Sin big-bang.

---

## Estado previo al roadmap

La auditoría detectó trabajo parcial ya existente:

| Pieza | Estado |
|-------|--------|
| `QueueManager` + `PlayerQueue` | ✔ Integrado en MusicPlayerService |
| `playback-history.ts` (repeat/shuffle) | ✔ Integrado |
| `PlaybackEngine` wrapper | ✔ Integrado |
| `FavoritesStore` | ✔ Adoptado por FavoriteBtn |
| `PlayerController` | Creado, **no adoptado por UI** |
| `PlaybackStore` | Creado, **no adoptado por UI** |
| Tests parciales | `player-queue.spec.ts`, `playback-history.spec.ts` |

Las fases 0–2 deben **completar y conectar** este trabajo, no duplicarlo.

---

## Resumen de fases

| Fase | Nombre | Duración est. | Objetivo |
|------|--------|---------------|----------|
| 0 | Preparación | 1–2 días | Contratos, feature flag, QA baseline |
| 1 | Store + Engine + Providers | 1–2 sem | PlaybackStore real, providers extraídos |
| 2 | Queue + Session | 1 sem | QueueManager conectado al store, persist completa |
| 3 | Resolver + Controller | 1 sem | Facade orquestador; UI empieza migración |
| 4 | UI unificación | 1–2 sem | Transport shared, TrackActions, queue drag |
| 5 | Favorites + Playlists | 3–5 días | Managers, reorder API+UI |
| 6 | Analytics + History | 1 sem | Stream v2, HistoryManager separado |
| 7 | Extensibilidad | ongoing | Lyrics, offline, IA, podcast, desktop |

**Total estimado MVP Spotify-like:** 6–8 semanas (1 dev senior)

---

## Fase 0 — Preparación

### Objetivos

- Formalizar interfaces TypeScript en `playback-core/models/`.
- Feature flag `USE_PLAYBACK_CORE` en environment.
- QA checklist baseline del player actual.
- Inventario de consumidores `MusicPlayerService` (grep-driven).

### Entregables

- [ ] `playback-core/models/*.ts` (interfaces domain)
- [ ] `environments/feature-flags.ts`
- [ ] `docs/playback/QA_CHECKLIST.md`
- [ ] Lista consumidores MusicPlayerService documentada

### Archivos

| Acción | Archivo |
|--------|---------|
| Crear | `apps/frontend/src/app/playback-core/models/*.ts` |
| Crear | `apps/frontend/src/environments/feature-flags.ts` |
| Crear | `docs/playback/QA_CHECKLIST.md` |
| Revisar | `apps/frontend/src/app/playback-core/*` (ya parcial) |

---

## Fase 1 — Playback Store + Engine + Providers

### Objetivos

- `PlaybackStore` con **read + write** (reemplazar facade read-only actual).
- Extraer providers de `PlayerPlaybackEngine` + `YoutubeEngineService`.
- Engine testeable aislado.
- **Sin cambiar UI** todavía.

### Tareas

1. Implementar `playback.store.ts` con reducers/effects.
2. `YouTubeAudioProvider` desde `YoutubeEngineService`.
3. `HtmlDemoProvider` desde demo WAV logic.
4. `ProviderManager` con fallback chain.
5. Unit tests engine attach/detach, ended, error.

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `shared/services/player/player-playback.engine.ts` | Mover lógica → providers |
| `shared/services/youtube-engine.service.ts` | Wrap as provider |
| `playback-core/playback.engine.ts` | Engine real attach/detach |
| `playback-core/playback.store.ts` | Reimplementar con write path |
| `shared/services/music-player.service.ts` | Sin eliminar — preparar delegación |

### Archivos a crear

- `playback-core/store/playback.state.ts`
- `playback-core/store/playback.selectors.ts`
- `playback-core/providers/provider.manager.ts`
- `playback-core/providers/youtube.provider.ts`
- `playback-core/providers/html-demo.provider.ts`
- `playback-core/providers/provider.interface.ts`

### Criterios de aceptación

- [ ] Tests engine ≥ 80% paths críticos
- [ ] Provider fallback en aislamiento
- [ ] Store refleja playing/paused/position sin UI

---

## Fase 2 — Queue Manager + Session

### Objetivos

- Conectar `QueueManager` al `PlaybackStore` (eliminar espejo signals en god service).
- Consolidar `playback-history.ts` → `queue.logic.ts`.
- `SessionPersistence` unificado.
- Bootstrap restore antes de primer play.

### Tareas

1. Queue mutations → store dispatch.
2. Migrar `player-session.storage.ts` → `session.persistence.ts`.
3. Validar restore cola + history stack + position.

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `playback-core/queue.manager.ts` | Emit to store |
| `shared/services/player/player-session.storage.ts` | Migrar |
| `shared/services/music-player.service.ts` | Usar store internamente |

### Criterios de aceptación

- [ ] Refresh restaura cola + track (paused)
- [ ] Repeat all/one/off funcionan via store
- [ ] remove/move bump queueRevision

---

## Fase 3 — Audio Resolver + Player Controller

### Objetivos

- `AudioResolver` injectable desde `PlayerSourceResolver`.
- `PlayerController` como **orquestador real** (no thin delegate).
- `onEnded` → controller.next().
- Feature flag para rutas críticas.

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `shared/services/player/player-source.resolver.ts` | Deprecar → audio.resolver.ts |
| `playback-core/player.controller.ts` | Reimplementar orquestación |
| `shared/services/music-player.service.ts` | Adapter deprecated |

### Archivos a crear

- `playback-core/resolver/audio.resolver.ts`
- `playback-core/adapters/track.adapter.ts`

### Criterios de aceptación

- [ ] Play completo vía Controller (flag ON)
- [ ] Paridad con MusicPlayerService (flag OFF)
- [ ] Autoplay via QueueManager.append

---

## Fase 4 — UI unificación

### Objetivos

- `PlayerTransportControlsComponent` compartido.
- `TrackActionsComponent` (play, favorite, queue, playlist).
- `QueuePanelComponent` con drag-drop (CDK).
- Search play inline.
- Migrar **todos** los componentes a `PlayerController`.

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `shared/components/player-bar/*` | Thin → Controller |
| `shared/components/now-playing-view/*` | Thin + QueuePanel |
| `shared/components/track-row/*` | TrackActions |
| `shared/components/media-card/*` | TrackActions |
| `packages/streaming/search/*` | Play inline |
| `packages/streaming/home/*` | Favorite en continue tiles |

### Archivos a crear

- `shared/components/player-transport-controls/**`
- `shared/components/track-actions/**`
- `shared/components/queue-panel/**`

### Criterios de aceptación

- [ ] Un solo template transport controls
- [ ] Search y Home reproducen sin navegar
- [ ] Drag reorder cola funciona
- [ ] Zero componentes inyectando MusicPlayerService directamente

---

## Fase 5 — Favorites + Playlist Managers

### Objetivos

- `FavoritesManager` evoluciona `FavoritesStore`.
- `PlaylistManager` con cache + `playPlaylist`.
- Backend `PATCH playlists/{id}/tracks/reorder`.
- Drag reorder en playlist detail.

### Backend

| Archivo | Cambio |
|---------|--------|
| `apps/backend/app/packages/streaming/routes/playlists.py` | reorder endpoint |
| `apps/backend/app/packages/streaming/services/playlist_service.py` | reorder logic |

### Criterios de aceptación

- [ ] Reorder persiste DB + UI
- [ ] playPlaylist setea context en store
- [ ] FavoritesManager único inject

---

## Fase 6 — History + Stream Analytics

### Objetivos

- `HistoryManager` (UX) separado de `StreamAnalyticsManager` (warehouse).
- Frontend → `/api/v2/stream/*`.
- Evaluar deprecar `ListenStatsService` o derivar de analytics.

### Archivos a crear

- `playback-core/history/history.manager.ts`
- `playback-core/analytics/stream-analytics.manager.ts`

### Criterios de aceptación

- [ ] Play genera stream start
- [ ] Skip/next genera skip event
- [ ] KPIs dashboard reflejan reproducciones reales

---

## Fase 7 — Extensibilidad (ongoing)

| Sub-fase | Feature |
|----------|---------|
| 7a | Multi-provider metadata backend |
| 7b | LyricsManager + sync |
| 7c | OfflineManager + BlobProvider + PWA SW |
| 7d | PodcastProvider (HLS) |
| 7e | RadioManager (IA) |
| 7f | Desktop shell (Electron/Tauri) |

---

## Lista completa de archivos a modificar

### Frontend — Core (alta prioridad)

```
apps/frontend/src/app/shared/services/music-player.service.ts
apps/frontend/src/app/shared/services/player/player-queue.ts
apps/frontend/src/app/shared/services/player/player-playback.engine.ts
apps/frontend/src/app/shared/services/player/player-source.resolver.ts
apps/frontend/src/app/shared/services/player/player-track.factory.ts
apps/frontend/src/app/shared/services/player/player-session.storage.ts
apps/frontend/src/app/shared/services/youtube-engine.service.ts
apps/frontend/src/app/shared/models/player.models.ts
apps/frontend/src/app/shared/config/demo-audio.config.ts
apps/frontend/src/app/playback-core/queue.manager.ts
apps/frontend/src/app/playback-core/playback.engine.ts
apps/frontend/src/app/playback-core/playback.store.ts
apps/frontend/src/app/playback-core/player.controller.ts
apps/frontend/src/app/playback-core/favorites.store.ts
apps/frontend/src/app/playback-core/playback-history.ts
```

### Frontend — UI

```
apps/frontend/src/app/shared/components/player-bar/*
apps/frontend/src/app/shared/components/now-playing-view/*
apps/frontend/src/app/shared/components/track-row/*
apps/frontend/src/app/shared/components/media-card/*
apps/frontend/src/app/shared/components/track-context-menu/*
apps/frontend/src/app/shared/components/favorite-btn/*
apps/frontend/src/app/shared/components/add-to-playlist-btn/*
apps/frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.*
```

### Frontend — Páginas consumidoras (playTrack / setQueue)

```
apps/frontend/src/app/packages/streaming/home/*
apps/frontend/src/app/packages/streaming/tracks/*
apps/frontend/src/app/packages/streaming/artist-detail/*
apps/frontend/src/app/packages/streaming/liked/*
apps/frontend/src/app/packages/streaming/playlists/*
apps/frontend/src/app/packages/streaming/track-detail/*
apps/frontend/src/app/packages/streaming/search/*
apps/frontend/src/app/packages/history/*
apps/frontend/src/app/packages/recommendations/*
apps/frontend/src/app/packages/analytics/trending/*
apps/frontend/src/app/features/tracks/*
```

### Frontend — Servicios relacionados

```
apps/frontend/src/app/packages/streaming/services/favorites.service.ts
apps/frontend/src/app/packages/streaming/services/playlists.service.ts
apps/frontend/src/app/packages/streaming/services/history.service.ts
apps/frontend/src/app/packages/streaming/services/listen-stats.service.ts
apps/frontend/src/app/packages/streaming/services/tracks.service.ts
apps/frontend/src/app/shared/services/track-cover.service.ts
```

### Backend

```
apps/backend/app/packages/streaming/services/audio_source_service.py
apps/backend/app/packages/streaming/routes/tracks.py
apps/backend/app/packages/streaming/routes/playlists.py
apps/backend/app/packages/streaming/services/playlist_service.py
apps/backend/app/api/routes/streaming.py
apps/backend/app/services/streaming_service.py
```

### Nuevos (~25–35 archivos en playback-core + 3 componentes shared)

```
apps/frontend/src/app/playback-core/store/*
apps/frontend/src/app/playback-core/providers/*
apps/frontend/src/app/playback-core/resolver/*
apps/frontend/src/app/playback-core/adapters/*
apps/frontend/src/app/playback-core/playlists/*
apps/frontend/src/app/playback-core/history/*
apps/frontend/src/app/playback-core/analytics/*
apps/frontend/src/app/playback-core/session/*
apps/frontend/src/app/shared/components/player-transport-controls/**
apps/frontend/src/app/shared/components/track-actions/**
apps/frontend/src/app/shared/components/queue-panel/**
```

**Estimado total:** ~60–80 archivos tocados, ~30–40 nuevos.

---

## Riesgos consolidados

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R1 | Big-bang migration breaks player | Media | Alto | Adapter + feature flag por fase |
| R2 | Facades huérfanos confunden al equipo | Alta | Medio | Migrar UI en F3-F4; documentar |
| R3 | YouTube API/iframe policy changes | Media | Alto | Provider abstraction + demo fallback |
| R4 | yt-dlp backend failures | Alta | Medio | Cache agresivo, retry, demo |
| R5 | Session restore autoplay blocked | Alta | Bajo | Restore paused; user gesture |
| R6 | Stream v2 auth/CORS issues | Media | Medio | Integration tests early F6 |
| R7 | Queue persist stale track IDs | Baja | Medio | Validate on restore, prune |
| R8 | Duplicate state during migration | Alta | Medio | Single write path via Controller |
| R9 | Performance drag-drop large queues | Baja | Bajo | Virtual scroll |
| R10 | Scope creep fase 7 | Media | Alto | Strict phase gates |

---

## Dependencias

### Técnicas

| Dependencia | Fase | Notas |
|-------------|------|-------|
| Angular 17+ signals | 1 | En proyecto |
| RxJS interop | 1–3 | Facade Favorites legacy |
| @angular/cdk/drag-drop | 4 | Queue + playlist reorder |
| FastAPI audio-source | 1–3 | Sin cambios |
| yt-dlp + YouTube API | 1 | Backend |
| DuckDB app_track_audio_source | 1 | Cache |
| Stream v2 API | 6 | fact_streaming |
| IndexedDB / SW | 7c | Offline |
| hls.js | 7d | Podcasts |

### Organizacionales

- QA checklist manual por fase
- Code review: prohibir nuevos PlayableTrack builders fuera de TrackAdapter
- Actualizar docs en `docs/playback/` cada fase

### Bloqueadores

- Fase 6 bloqueada si v2 stream no acepta tokens del frontend
- Fase 5 reorder bloqueada sin endpoint backend

---

## Beneficios por fase

| Fase | Beneficio inmediato |
|------|---------------------|
| 0 | Contratos claros, baseline QA |
| 1 | Engine testeable, providers aislados |
| 2 | Cola en store único, session robusta |
| 3 | API única PlayerController |
| 4 | UX Spotify-grade, cero duplicación UI |
| 5 | Playlists reorder, favorites centralizados |
| 6 | Analytics warehouse confiables |
| 7 | Plataforma multi-año sin rewrite |

---

## Definición de Done — MVP Spotify Desktop (fin Fase 4–6)

- [ ] Un solo PlaybackStore adoptado por toda la UI
- [ ] Cola global persistente en sesión
- [ ] Repeat off/all/one + shuffle (ya existe lógica — conectar al store)
- [ ] Queue editable (remove, reorder drag, add next)
- [ ] Favoritos desde cualquier superficie de track
- [ ] Playlists play + reorder tracks
- [ ] PlayerBar + NowPlaying sin duplicación lógica
- [ ] Stream events en warehouse
- [ ] MusicPlayerService eliminado
- [ ] Zero PlayableTrack factories duplicadas (solo TrackAdapter)

---

## Orden de implementación

```
F0 → F1 → F2 → F3 → F4 → F5 → F6 → F7*
         ↑__________________|
         (F3 puede solaparse final F2)
```

---

## Próximo paso

**Esperar autorización del usuario** para iniciar Fase 0. Hasta entonces: solo auditoría y diseño — **sin cambios de código de producción**.

---

*Fin del roadmap — referencia: AUDIT (estado actual), ARCHITECTURE V2 (diseño).*
