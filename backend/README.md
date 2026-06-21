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
    └── test_api.py             # 12 tests mínimos
```

## Comandos

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/test_api.py -v
```

OpenAPI: http://localhost:8000/docs
