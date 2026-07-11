# Backend — VOXMETRIK_V2 API

FastAPI + DuckDB warehouse (medallion). Entry point: `app/main.py`.

## Architecture

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py          # DB_PATH, API_PREFIX, CORS, ENV
│   │   ├── database.py        # get_connection(), read pool, fetch helpers
│   │   └── logging.py
│   ├── api/
│   │   ├── enterprise_router.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── dashboards.py
│   │       ├── enterprise_analytics.py
│   │       ├── enterprise_users.py
│   │       └── tracks.py
│   ├── services/
│   │   ├── enterprise_analytics_service.py
│   │   ├── enterprise_user_service.py
│   │   └── track_service.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── analytics_repository.py
│   │   ├── user_repository.py
│   │   └── track_repository.py
│   ├── schemas/
│   │   ├── common.py          # { status, data, meta }
│   │   ├── analytics.py
│   │   ├── user.py
│   │   └── track.py
│   ├── sql/                   # Optimized warehouse queries
│   └── utils/
│       ├── sql_loader.py
│       └── time_utils.py
├── requirements.txt
└── tests/
```

**Layers:** `API → Service → Repository → DuckDB`

Scripts operativos: [`../scripts/README.md`](../scripts/README.md) · Mapa repo: [`../docs/02-architecture/structure.md`](../docs/02-architecture/structure.md)

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Set warehouse path (optional — auto-detects `data/warehouse/voxmetrik.duckdb`):

```bash
export DB_PATH=/path/to/voxmetrik.duckdb
```

Docker (from repo root): `make up`

## Enterprise endpoints (`/api/v1`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health (warehouse, ETL, row counts) |
| GET | `/api/v1/dashboard/overview` | KPIs, genres, artists, devices, growth |
| GET | `/api/v1/analytics/streams` | `start_date`, `end_date` — series + peak hours |
| GET | `/api/v1/tracks/top` | Top tracks (`agg_tracks_populares`) |
| GET | `/api/v1/users/{id}/insights` | Engagement, plays, skips, favorites |
| GET | `/api/v1/tracks/recommendations/{user_id}` | Statistical recs (`agg_recommendation_scores`) |

Response envelope:

```json
{
  "status": "success",
  "data": {},
  "meta": { "count": 10, "source": "duckdb" }
}
```

## Tests

```bash
pytest tests/test_enterprise_api.py -v
pytest tests/ -q
```

OpenAPI: http://localhost:8000/docs
