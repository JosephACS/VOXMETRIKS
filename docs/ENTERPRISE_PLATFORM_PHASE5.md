# ENTERPRISE PLATFORM — Fase 5

**Fecha:** 2026-07-05  
**Alcance:** Observabilidad, notificaciones, tiempo real, caché, jobs, seguridad, CI  
**Prerequisitos:** Fases 1–4 intactas

---

## Arquitectura

```
app/platform/
├── observability/status.py   → estado unificado de subsistemas
├── notifications/            → store + service + modelos
├── realtime/hub.py           → SSE in-process (opcional)
├── jobs/scheduler.py         → asyncio scheduler ligero
├── jobs/tasks.py             → refresh cache, métricas, audio probe
└── routes/platform.py        → API /api/v1/platform/*
```

---

## Observabilidad

| Endpoint | Auth | Descripción |
|----------|------|-------------|
| `GET /api/v1/platform/health/subsystems` | Público | Resumen warehouse, reco, audio, jobs |
| `GET /api/v1/platform/status` | Engineer | Estado completo |
| `GET /api/v1/platform/metrics` | Engineer | Métricas básicas |

Subsistemas reportados: warehouse, playback (client), audio resolver, recommendations, cache, jobs, notifications.

Logs estructurados existentes en `app/core/logging.py`. Errores uniformes vía `error_handlers.py` — sin stacktrace al cliente en producción.

---

## Notificaciones internas

- Backend: `NotificationService` emite eventos tipados (`favorite_added`, `pipeline_run`, etc.)
- Frontend: `NotificationService` + `NotificationToastComponent` (sin `alert()`)
- Favoritos: toast en cliente + notificación server al agregar favorito

---

## Tiempo real

| Modo | Implementación |
|------|----------------|
| **SSE** | `GET /api/v1/platform/events` (backend listo, `SSE_ENABLED=true`) |
| **Polling** | Frontend `PlatformEventsService` — cada 30s a `/platform/notifications` |

WebSocket documentado como siguiente paso (requiere auth en handshake).

---

## Caché

TTL configurable por dominio en `.env`:

- `CACHE_TTL_SMART_HOME` — home personalizada
- `CACHE_TTL_RECOMMENDATIONS` — ranking
- `CACHE_TTL_AUDIO` — resolución audio

Smart home cacheada en `SmartRecommendationService.get_home()`. Invalidación periódica vía job `task_refresh_recommendations_cache`.

---

## Background jobs

Scheduler asyncio en lifespan (`JOBS_ENABLED`, `JOBS_INTERVAL_SEC`):

1. `task_record_metrics`
2. `task_refresh_recommendations_cache`
3. `task_validate_audio_sources`
4. `task_clean_stale_cache`

Desactivado automáticamente en pytest/E2E.

---

## Seguridad

- `/platform/status` y `/metrics` requieren rol **engineer**
- Notificaciones requieren autenticación
- CORS/docs/seeds condicionados por `ENVIRONMENT=production`
- Rate limits configurables (in-memory, local)

---

## CI/CD

Workflow opcional: `.github/workflows/ci.yml`

- Backend: pytest subset Phase 5 + 6 + smart
- Frontend: vitest + build

---

## Validación local

```bash
cd apps/backend
python -m pytest tests/test_platform_phase5.py tests/test_ai_phase6.py -q

cd apps/frontend
npm run test
npm run build
```

---

## Pendientes

- Redis opcional para cache/rate-limit distribuido
- WebSocket con auth
- Prometheus `/metrics`
- Auth en enterprise dashboard analytics (legacy)

---

*Fase 5 — Enterprise Platform.*
