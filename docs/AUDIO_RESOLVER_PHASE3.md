# AUDIO RESOLVER — Fase 3

**Fecha:** 2026-07-05  
**Alcance:** Resolución multiproveedor, caché inteligente, fallback automático  
**Prerequisitos:** Fase 1 (UX Core) + Fase 2 (Playback Engine)

---

## Objetivo

Maximizar la tasa de reproducción del catálogo (metadatos tipo Spotify) usando fuentes legales disponibles, con fallback automático y errores amigables. **No garantiza reproducción universal.**

---

## Arquitectura

```
Frontend                          Backend
────────                          ───────
MusicPlayerService                GET /api/v1/tracks/{id}/audio-source
       │                                    │
       ▼                                    ▼
AudioResolver (playback-core)     audio_source_service
       │                                    │
       │ resolvePlayableSource()            ▼
       │                            AudioResolver
       │                                    │
       ▼                            ┌────────┴────────┐
PlaybackEngine                    │                 │
(youtube | stream | demo)    YouTubeProvider   AudiusProvider
                                    │                 │
                                    └────────┬────────┘
                                             ▼
                                  app_track_audio_source (DuckDB cache)
```

### Principio clave

Los componentes Angular **no conocen proveedores**. Solo `AudioResolver` traduce la respuesta API → modo del engine (`youtube`, `stream`, `demo`).

---

## Interfaz de proveedores (backend)

```python
class AudioProvider(ABC):
    @property
    def name(self) -> str: ...

    def resolve(self, track: TrackContext) -> ResolvedSource: ...

    def validate(self, source_ref, playable_url) -> bool: ...
```

---

## Proveedores

| Proveedor | Estado | Requisitos | Notas |
|-----------|--------|------------|-------|
| **YouTube** | ✅ Implementado | yt-dlp (sin key) + YouTube IFrame | Primario; scoring heurístico |
| **Audius** | ✅ Implementado | API pública sin key | Stream HTML5 vía `playable_url` |
| **Demo local** | ✅ Frontend | 8 WAV en `/assets/audio/` | Último recurso antes de error |
| **Jamendo** | ⏸ Pendiente | Requiere `client_id` | No disponible en proyecto |
| **Archive.org** | ⏸ Pendiente | Baja relevancia para catálogo pop | Evaluar en Fase 4 |
| **Spotify embed** | ⏸ Pendiente | OAuth + Premium | Catálogo tiene `spotify_track_id` |

---

## Flujo de fallback

```
1. Caché app_track_audio_source (status=ok, failure_count < 3)
2. YouTubeProvider (yt-dlp → YouTube Data API backup)
3. AudiusProvider (search + stream URL)
4. Frontend: demo WAV determinístico
5. Error amigable + auto-skip en cola
```

Si un proveedor falla en reproducción, el frontend llama `GET ...?force=true&skip_provider=youtube` para intentar el siguiente.

---

## Caché inteligente

**Tabla:** `app_track_audio_source`

| Columna | Uso |
|---------|-----|
| `track_id` | PK |
| `provider` | youtube \| audius |
| `youtube_video_id` | Retrocompat (YouTube) |
| `source_ref` | ID genérico del proveedor |
| `playable_url` | URL stream (Audius) |
| `query` | Query de búsqueda |
| `status` | ok \| not_found \| error \| pending |
| `failure_count` | Incrementa en fallos de playback |
| `confidence_score` | 0–1 heurístico |
| `resolved_at` / `last_checked_at` | Timestamps |

Migración segura vía `migrate_audio_source_columns()` — no rompe datos existentes.

---

## API (retrocompatible)

```
GET /api/v1/tracks/{id}/audio-source
  ?force=false
  &async_resolve=true
  &skip_provider=youtube   # nuevo — fallback tras error
```

**Respuesta extendida (campos nuevos opcionales):**

```json
{
  "track_id": 42,
  "provider": "audius",
  "youtube_video_id": null,
  "source_ref": "abc123",
  "playable_url": "https://api.audius.co/v1/tracks/abc123/stream?app_name=VOXMETRIKS",
  "query": "Song Artist",
  "status": "ok",
  "confidence_score": 0.72
}
```

Campos legacy `youtube_video_id` y `provider` se mantienen.

---

## Frontend

### Archivos nuevos

| Archivo | Rol |
|---------|-----|
| `playback-core/resolver/audio.resolver.ts` | Resolver central (`resolvePlayableSource`) |
| `playback-core/resolver/resolved-source.model.ts` | Tipos + mapeo API |
| `playback-core/resolver/audio-resolver.phase3.spec.ts` | Tests |

### Cambios

| Archivo | Cambio |
|---------|--------|
| `music-player.service.ts` | Usa `AudioResolver`; modo `stream` para Audius |
| `tracks.service.ts` | `skipProvider` query param |
| `api.models.ts` | Campos `source_ref`, `playable_url`, `confidence_score` |
| `player-source.resolver.ts` | Deprecated re-export |

### Modos del engine

| Modo | Fuente |
|------|--------|
| `youtube` | YouTube IFrame |
| `stream` | HTML5 Audio (Audius URL) |
| `demo` | WAV local |
| `loading` | Resolviendo |

### Mensaje de error

> No se encontró una fuente reproducible para esta canción.

---

## Logging interno

Logger: `voxmetriks.audio.resolver`

Registra: track_id, provider, outcome, elapsed_ms, cache hit, fallback, errors.

No expuesto al usuario.

---

## Manejo de errores

1. Proveedor falla en playback → `recoverFromPlaybackError` con `skip_provider`
2. Todos fallan → demo WAV
3. Demo falla → error amigable + `next()` si hay cola/autoplay
4. `failure_count` incrementa en backend (API `report_source_failure` preparada)

---

## Pruebas ejecutadas

```bash
# Backend
cd apps/backend
python -m pytest tests/test_audio_source.py tests/test_audio_resolver.py -q
# ✅ 10/10 passed

# Frontend
cd apps/frontend
npm run test   # ✅ 49/49 passed
npm run build  # ✅ OK
npm run lint   # ⚠️ 1 error preexistente (features/tracks/tracks.component.ts)
```

### Cobertura Fase 3

| # | Caso | Archivo |
|---|------|---------|
| 1 | Fuente cacheada reutilizada | `test_audio_resolver.py` |
| 2 | Resolución sin caché | `audio-resolver.phase3.spec.ts` |
| 3 | Fallback YouTube → Audius | `test_audio_resolver.py` |
| 4 | Todos fallan → not_found | ambos |
| 5 | Error no congela (demo fallback) | `audio-resolver.phase3.spec.ts` |
| 6 | Recovery skip_provider | ambos |
| 7 | API retrocompatible | schema + tests |
| 8 | No re-busca si caché válida | `test_audio_resolver.py` |

Playwright: no ejecutado. pytest backend: ✅.

---

## Pendientes Fase 4

- Jamendo (requiere API key)
- Archive.org (baja prioridad)
- Spotify embed con `spotify_track_id`
- Validación activa de URLs cacheadas (HEAD request)
- Métricas de cobertura por proveedor en analytics
- Drag reorder cola / stream analytics v2

---

## Compatibilidad Fase 1 + 2

- Favoritos, cola global, TrackActions: intactos
- Controles, persistencia, historial: intactos
- Endpoint `/audio-source`: retrocompatible
- YouTube sigue siendo proveedor primario

---

*Fase 3 completada — arquitectura multiproveedor, fallback, caché, tests OK.*
