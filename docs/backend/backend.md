# Backend — FastAPI

## Stack

| Componente | Versión | Rol |
|------------|---------|-----|
| Python | 3.12 | Runtime |
| FastAPI | 0.111 | Framework HTTP |
| Uvicorn | 0.30 | ASGI server |
| Pydantic | 2.7 | Validación / schemas |
| DuckDB | 1.1 | Warehouse embebido |

## Estructura de directorios

```
apps/backend/app/
├── main.py                 # Entry point, lifespan, routers
├── api/                    # Capa HTTP
│   ├── router.py           # /api/v2
│   ├── enterprise_router.py# /api/v1 enterprise
│   ├── deps.py             # Dependencias V2
│   ├── deps_enterprise.py  # DI enterprise
│   └── routes/             # Endpoints por dominio
├── core/                   # Infraestructura transversal
│   ├── config.py           # pydantic-settings
│   ├── logging.py          # JSON + rotación
│   ├── cache.py            # TTL in-process
│   ├── middleware.py       # Request timing
│   ├── security.py         # CORS, headers, rate limit
│   ├── error_handlers.py   # Envelope uniforme
│   └── query_params.py     # Paginación / filtros
├── services/               # Lógica de negocio
├── repositories/           # Acceso DuckDB read-only
├── db/                     # DuckDBClient singleton
├── etl/                    # Medallion builders
├── packages/               # Legacy domain modules
├── schemas/                # Pydantic enterprise
├── models/                 # DTOs V2
└── sql/                    # Queries externalizadas
```

## Patrón de capas

```
Route → Service → Repository → DuckDBClient
              ↘ Cache (TTL)
```

### Repositories (4 + base)

| Clase | Responsabilidad |
|-------|-----------------|
| `BaseRepository` | `fetch_all/one/scalar`, `table_exists` |
| `AnalyticsRepository` | GOLD: streams, genres, artists, devices |
| `TrackRepository` | Top tracks, recommendations SQL |
| `UserRepository` | User insights |

### Services principales

| Servicio | Dominio |
|----------|---------|
| `EnterpriseAnalyticsService` | Dashboard + streams analytics |
| `TrackService` | Top tracks + recomendaciones |
| `EnterpriseUserService` | User insights |
| `RecommendationEngine` | Scoring heurístico ponderado |
| `HealthService` | `/health` |
| `DashboardService` (V2) | Dashboard modular |
| Packages `*Service` | Legacy streaming/auth |

## Boot sequence (lifespan)

1. `run_system_boot()` — ETL → GOLD → cache → validate
2. `bootstrap_database()` — verificar warehouse
3. `ensure_user_tables` / `ensure_app_tables` — tablas app
4. `open_read_pool()` — pool lectura DuckDB
5. Shutdown: cerrar conexiones

Variable `SKIP_SYSTEM_BOOT=1` desactiva boot en tests.

## Middleware stack

| Orden | Middleware | Función |
|-------|------------|---------|
| 1 | CORS | Orígenes configurables |
| 2 | SecurityHeaders | X-Frame-Options, HSTS (prod) |
| 3 | GlobalRateLimit | Protección abuse |
| 4 | RequestContext | X-Request-ID |
| 5 | RequestTiming | X-Response-Time-Ms, logs |

## Configuración

Toda la config vive en `app/core/config.py` via variables de entorno. Ver [deployment.md](../deployment/deployment.md).

## Ejecución local

```bash
cd apps/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest tests/ -v
```

Ver [testing.md](../testing/testing.md).
