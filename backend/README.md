# Backend — Voxmetriks API

FastAPI + DuckDB. Punto de entrada: `app/main.py`.

**Documentación del proyecto:** [README.md](../README.md) · **Arranque:** [docs/QUICKSTART.md](../docs/QUICKSTART.md)

## Estructura actual

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, /health, routers
│   ├── core/                   # config, database
│   ├── packages/
│   │   ├── users/              # login, register, profile
│   │   ├── streaming/          # catalog, playlists, favorites
│   │   └── analytics/          # stats, analytics, explorer
│   └── shared/schemas/
└── tests/
    ├── conftest.py             # DuckDB aislada para pytest
    ├── test_api.py             # health, login, playlists, favorites
    ├── test_auth_security.py   # bcrypt, logout, health exposure
    ├── test_analytics_security.py
    ├── test_smoke_regression.py
    ├── test_text_search.py
    └── test_display_text.py
```

## Comandos

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
python ../scripts/smoke_api.py --base-url http://localhost:8000
python ../scripts/smoke_user_journey.py --base-url http://localhost:8000
```

OpenAPI: http://localhost:8000/docs
