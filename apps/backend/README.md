# Backend — VOXMETRIKS API

FastAPI + DuckDB warehouse (medallion). Entry point: `app/main.py`.

## Architecture (mapa actual)

```
apps/backend/
├── app/
│   ├── main.py
│   ├── core/                 # config, database, logging, security
│   ├── packages/             # package-by-domain (identity, billing, …)
│   ├── shared/               # schemas / utilidades compartidas
│   └── etl/                  # refresh runtime (no sustituye analytics/elt)
├── scripts/                  # seeds, smokes y utilidades del backend
├── requirements.txt
└── tests/
```

**Layers:** presentación → application/domain → infrastructure → DuckDB (por package).

Scripts operativos del monorepo: [`../../automation/scripts/README.md`](../../automation/scripts/README.md).
Mapa de estructura del repo: [`../../docs/architecture/structure.md`](../../docs/architecture/structure.md).

## Run

```bash
cd apps/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Warehouse (opcional — auto-detecta `data/warehouse/voxmetrik.duckdb`):

```bash
# desde la raíz
python analytics/elt/pipelines/elt_pipeline.py
export DB_PATH=/path/to/voxmetrik.duckdb
```

Docker (desde la raíz del repo): `make pipeline` luego `make up` / `docker compose up --build`.

## Tests

```bash
cd apps/backend
python -m pytest -q
```

OpenAPI: http://localhost:8000/docs
