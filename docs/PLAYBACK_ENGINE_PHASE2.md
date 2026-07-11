# PLAYBACK ENGINE — Fase 2

**Fecha:** 2026-07-05  
**Alcance:** Motor de reproducción profesional, cola avanzada, persistencia, controles, errores  
**Prerequisito:** Fase 1 (favoritos globales, cola global, TrackActions)  
**Backend:** Sin cambios — `GET /api/v1/tracks/{id}/audio-source`

---

## Qué se implementó

### 1. Controles completos del reproductor

| Control | Estado |
|---------|--------|
| Play / Pause / Resume | ✅ |
| Next / Previous | ✅ |
| Seek + barra progreso | ✅ |
| Volume + Mute | ✅ (persistidos) |
| Repeat off / all / one | ✅ ciclo UI + badge "1" |
| Shuffle | ✅ en next y onEnded |
| Autoplay al fin de cola | ✅ |
| Duración + progreso | ✅ PlayerBar + NowPlaying |

### 2. Cola avanzada

- Ver cola completa en **Now Playing**
- Eliminar pista (×)
- Limpiar cola pendiente
- **Reordenar** pistas pendientes (↑↓) vía `moveInQueue`
- Reproducir pista específica (click en fila)
- **Historial previous** independiente (`PlaybackHistoryStack`)
- Next respeta shuffle/repeat

### 3. Persistencia

| Dato | Storage | Key |
|------|---------|-----|
| volume, muted, shuffle, repeatMode, autoplay | `localStorage` | `vox:playback:prefs` |
| track, queue, index, currentTime, playHistory | `sessionStorage` | `vox:playback:session` |

**Navegar rutas:** singleton services mantienen estado en memoria; debounce 300ms persiste sesión.

**Refresh:** restaura track, cola, posición, prefs — **estado `paused`** (sin autoplay con sonido). Usuario pulsa Play para continuar.

**YouTube tras refresh:** video se **cue** sin autoplay; posición se restaura al pulsar Play (`pendingRestoreTime`).

### 4. Manejo de errores de audio

```
YouTube error → recoverFromYoutubeError (1 retry force) → demo fallback
Demo falla   → playbackError + status error
             → auto next() tras 1.2s si hay cola/autoplay
             → botón Reintentar en PlayerBar
```

### 5. Estados del player

```typescript
type PlaybackStatus = 'idle' | 'loading' | 'playing' | 'paused' | 'buffering' | 'error';
```

- **`buffering`**: HTML5 `waiting`/`playing` + YouTube state 3
- UI muestra "Buffering…" / "Cargando…" en PlayerBar

### 6. Experiencia de usuario (PlayerBar)

Título, artista, portada, favorito, play/pause, next/previous, progreso, duración, volumen, shuffle/repeat, cola (pill + Now Playing).

---

## Arquitectura final

```
UI (PlayerBar, NowPlayingView, TrackActions)
        │ read: PlaybackStore
        │ write: PlayerController
        ▼
MusicPlayerService (orquestador)
    ├── PlaybackEngine → PlayerPlaybackEngine (HTML5 + YouTube)
    ├── QueueManager → PlayerQueue + PlaybackHistoryStack
    ├── PlayerSourceResolver → TracksService.getAudioSource
    └── player-session.storage (prefs + session)

PlaybackStore expone: status, repeatMode, muted, playbackError, queue,
                     pendingQueue, playHistory, progressPct, etc.
```

---

## Cola + historial

### Next
`QueueManager.advance(shuffle, repeatMode)` → `nextIndex()` en `playback-history.ts`

### Previous
1. Si `currentTime > 3s` → seek 0
2. Si no → `PlaybackHistoryStack.pop()` (pistas ya reproducidas)
3. **No** usa retroceso circular en cola

### Historial
Se registra al **dejar** una pista (`loadTrack` con track distinto).

---

## Repeat / Shuffle

| Modo | Fin de track | Next en última |
|------|--------------|----------------|
| off | stop / autoplay | null |
| all | wrap | índice 0 |
| one | seek 0 + resume | mismo índice |
| shuffle | random | random |

---

## Persistencia — flujo

```
Cambio transporte/cola → schedulePersist (300ms) → sessionStorage
Cambio prefs → localStorage inmediato
Bootstrap → readPlaybackPrefs + restorePlaybackSession → paused
YouTube restore → cueVideo + pendingRestoreTime → seek on resume
```

---

## Errores de audio

- `playbackError` signal + mensaje en PlayerBar
- `retryCurrent()` limpia cache de retry y re-resuelve fuente
- Auto-skip no bloquea UI ni deja player congelado

---

## Archivos modificados / creados

### Nuevos
- `playback-core/playback-engine.phase2.spec.ts`

### Modificados (Fase 2)
- `shared/services/music-player.service.ts` — buffering, YouTube restore, pending seek
- `shared/services/player/player-playback.engine.ts` — hooks waiting/playing/buffering
- `shared/services/youtube-engine.service.ts` — onBuffering (state 3)
- `playback-core/playback.store.ts` — `playHistory` computed
- `shared/components/player-bar/*` — buffering UI
- `shared/components/now-playing-view/*` — reorder ↑↓, queue actions
- `core/i18n/locales/en.ts`, `es.ts` — buffering, moveUp/Down

### Sin cambios backend

---

## Pruebas ejecutadas

```bash
cd apps/frontend
npm run test   # ✅ 43/43 passed
npm run build  # ✅ OK (warnings budget preexistentes)
npm run lint   # ⚠️ error preexistente en features/tracks/tracks.component.ts
```

### Cobertura Fase 2 (`playback-engine.phase2.spec.ts`)

| # | Caso |
|---|------|
| 1 | Play/Pause funciona |
| 2 | Next reproduce siguiente en cola |
| 3 | Previous vuelve al historial |
| 4 | Shuffle cambia índice |
| 5 | Repeat one repite misma pista |
| 6 | Repeat all reinicia cola |
| 7 | Volumen persiste |
| 8 | Cola persiste en sessionStorage |
| 9 | Player no se reinicia (singleton) |
| 10 | Error de audio no bloquea + retry |

También: `playback-history.spec.ts`, `player-queue.spec.ts`, `music-player.service.spec.ts`, `playback-spotify-ux.phase1.spec.ts`.

Playwright: no ejecutado (suite en `automation/playwright/`).  
pytest: N/A (sin cambios backend).

---

## Pendientes Fase 3

- Múltiples proveedores de audio (Provider Manager)
- Drag-and-drop CDK en cola (API `moveInQueue` ya lista)
- Stream analytics v2
- Cross-tab / IndexedDB persistence
- Componente compartido `PlayerTransportControls`
- Migrar páginas restantes de `MusicPlayerService` directo → `PlayerController`

---

## Compatibilidad Fase 1

- Favoritos globales, TrackActions, cola global intactos
- `MusicPlayerService` sigue siendo orquestador interno (no breaking)
- `PlayerController` + `PlaybackStore` siguen siendo la API pública UI

---

*Fase 2 completada — build y tests OK.*
