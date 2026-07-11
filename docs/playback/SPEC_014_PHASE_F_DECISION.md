# Spec 014 Phase F — Playback decision (freeze)

**Fecha:** 2026-07-11  
**Alcance:** Solo documentación y verificación. **Sin migración de código.**  
**Ubicación canónica de docs de playback:** `docs/playback/`

---

## Decisión (normativa para 014)

1. **`MusicPlayerService`** es la **implementación activa** y la fuente de verdad práctica del transporte, cola mutada, resolución de audio, persistencia de sesión y señales de UI durante la spec 014.
2. **`playback-core`** es la **dirección futura** (fachada + managers + store). Hoy es **parcial**: varias piezas existen y se consumen, pero **delegan** en `MusicPlayerService` (no sustituyen el motor).
3. **No se elimina** ningún componente de reproducción hasta una spec de migración con paridad demostrable.
4. La UI debe converger a **una sola fuente de verdad**; hoy coexisten inyecciones directas de `MusicPlayerService` y de `PlayerController` (adaptador).
5. Los **providers** (YouTube, stream/Audius vía API, demo WAV) permanecen desacoplados detrás del resolver; el audio demo **no implica derechos comerciales**.
6. **No presentar** `playback-core` como “completamente implementado”: el diseño V2 en `PLAYBACK_ARCHITECTURE_V2.md` sigue siendo la meta; el código actual es un puente.

---

## Clasificación verificada en código (2026-07-11)

| Elemento | Clasificación | Evidencia |
|----------|---------------|-----------|
| `MusicPlayerService` | **ACTIVO** | Orquesta cola, engine, `AudioResolver`, persistencia (`player-session.storage`), history/listen-stats |
| `PlayerBar` / `NowPlayingView` | **ACTIVO** | Montados en `DashboardLayout`; barra usa `PlayerController` |
| `PlayerController` | **ADAPTADOR** | Facade → `MusicPlayerService` (`playback-core/player.controller.ts`) |
| `PlaybackStore` | **ADAPTADOR / PARCIAL** | Lee estado del player + `QueueManager`; mutaciones vía controller → service |
| `QueueManager` | **ACTIVO** | Inyectado por `MusicPlayerService` y store |
| `PlaybackEngine` (playback-core) | **ADAPTADOR** | Wrapper de `PlayerPlaybackEngine` + `YoutubeEngineService` |
| `AudioResolver` (FE) | **ACTIVO** | Usado por `MusicPlayerService`; modos youtube / stream / demo |
| Backend audio (YouTube → Audius → not found) | **ACTIVO** | `packages/streaming/services/audio/*`; tests `test_audio_resolver.py` |
| `FavoritesStore` (playback-core) | **PARCIAL** | Consumido p.ej. por `favorite-btn` |
| Diseño V2 completo (`PLAYBACK_ARCHITECTURE_V2.md`) | **PROPUESTO** | Documento de arquitectura futura |
| Consumo FE de `/api/v2/stream/*` para facts | **NO CONSUMIDO** / deuda | Analytics de stream de warehouse no alimentados por el player SPA |

### Consumidores UI (muestra)

- **Vía `PlayerController`:** home, search, playlists, media-card, track-row, track-context-menu, trending, smart widgets, player-bar.
- **Vía `MusicPlayerService` directo:** layout (estado expandido), artist-detail, top-tracks analytics, etc.

---

## Providers confirmados

| Provider | Rol |
|----------|-----|
| YouTube (IFrame / `YoutubeEngineService`) | Primario cuando hay `videoId` / resolución OK |
| Stream URL (Audius u otros vía `GET .../audio-source`) | Fallback de stream |
| Demo WAV locales | Fallback UX; **no** licencia comercial |

---

## Deudas documentadas (fuera de 014)

- Unificar UI para no mezclar `MusicPlayerService` vs `PlayerController`.
- Completar Playback Core V2 sin god-service (spec propia).
- Cablear analytics de reproducción reales a warehouse si el producto lo exige.
- Smoke interactivo G7 / Playwright no disponible en este entorno (`automation/playwright/node_modules` ausente).
- `AUDIT_PLAYBACK_CORE.md` (2026-07-05) afirma que la UI no consume playback-core; **ya no es exacto** — esta nota F prevalece para el estado 014.

---

## Pruebas ejecutadas (F — no destructivas)

| Prueba | Resultado |
|--------|-----------|
| `npm test` (Angular unit / Vitest) | **59 passed** / 12 files |
| `npm run lint` | **0 errors**, 13 warnings |
| `ng build` (development) | **PASS** |
| Backend `test_audio_resolver.py` + `test_audio_source.py` | **10 passed** |
| Playwright e2e | **No disponible** (`node_modules` ausente) |
| Smoke interactivo de reproducción en browser | **No ejecutado** (no sustituido por afirmación) |

**Código de reproducción:** cero cambios en esta fase.
