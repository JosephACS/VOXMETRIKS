# Performance — Rendimiento

## Estrategia general

1. **Leer AGG, no FACT** en dashboards y rankings.
2. **Cache in-process** con TTL configurable por dominio.
3. **Conexión DuckDB singleton** reutilizable (read-only pool).
4. **Queries externalizadas** en `apps/backend/app/sql/*.sql`.
5. **Paginación** en endpoints de listado grandes.

## Cache TTL

| Dominio | Variable | Default | Endpoints |
|---------|----------|---------|-----------|
| Dashboard | `CACHE_TTL_DASHBOARD` | 120s | `/dashboard/overview` |
| Analytics | `CACHE_TTL_ANALYTICS` | 90s | `/analytics/streams` |
| Top tracks | `CACHE_TTL_TOP_TRACKS` | 180s | `/tracks/top` |
| Recommendations | `CACHE_TTL_RECOMMENDATIONS` | 120s | `/tracks/recommendations/*` |

Desactivar: `CACHE_ENABLED=false`

## DuckDB

### Conexiones

- **Lectura:** `DuckDBClient` singleton + `open_read_pool()` legacy
- **Escritura:** `using_write_conn()` con lock exclusivo
- **Tests:** DB aislada en `tests/.pytest_db/`

### Optimización top tracks

`TrackRepository` detecta si `agg_tracks_populares.total_streams` existe:
- **Sí** → `top_tracks_agg.sql` (sin JOIN a fact_streaming)
- **No** → `top_tracks.sql` (fallback con JOIN)

### SQL timing

Todas las queries logean duración en `logs/database.log`:
```
sql label=repo_top_tracks elapsed_ms=12.5 params=[20]
```

## Recommendation Engine

Pipeline de scoring (sin ML):
1. Pool 1000 candidatos desde AGG
2. Score: 35% popularity + 25% engagement + 20% collaborative + 20% trending
3. Top N con cache

Complejidad: O(candidates × factors) — ~ms en warehouse local.

## Frontend

- **Lazy loading:** 27 rutas con `loadComponent`
- **OnPush** en componentes shared
- **RxJS:** `takeUntilDestroyed`, `catchError`, `forkJoin` paralelo en dashboard
- **Polling:** dashboard refresh cada 30s (configurable en componente)

## Benchmarks orientativos (local, warehouse ~100k)

| Operación | Tiempo típico |
|-----------|---------------|
| GET /health | < 50 ms |
| GET /dashboard/overview (cold) | 100–500 ms |
| GET /dashboard/overview (cached) | < 5 ms |
| GET /tracks/top | 50–200 ms |
| Recommendations (cold) | 200–800 ms |

## Limitaciones conocidas

| Limitación | Impacto | Mitigación futura |
|------------|---------|-------------------|
| Cache in-process | No compartido entre workers | Redis |
| DuckDB single-file | Write lock serializa | Read replicas / Snowflake |
| In-memory rate limit | No distribuido | Redis rate limiter |
| Polling 30s dashboard | Carga innecesaria | WebSockets / SSE |

## Checklist optimización queries

- [ ] Usar columnas explícitas (no `SELECT *`)
- [ ] Preferir `agg_*` sobre `fact_*`
- [ ] Parametrizar con `?` bindings
- [ ] LIMIT en todos los listados
- [ ] Índices secundarios (`core/indexes.py`)
