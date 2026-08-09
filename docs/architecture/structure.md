# Estructura del repositorio

Mapa oficial del monorepo **Voxmetriks** (post-consolidación documental).

```
voxmetriks/
├── apps/
│   ├── backend/                  # FastAPI
│   └── frontend/                 # Angular SPA
├── analytics/elt/                # Pipeline Medallion → DuckDB
├── automation/
│   ├── scripts/
│   ├── e2e/
│   └── playwright/               # Config Playwright (reports locales)
├── infrastructure/
│   ├── docker/                   # Dockerfile canónico backend+ELT
│   ├── airflow/                  # Spec 048 Airflow LocalExecutor (demo)
│   ├── pocketbase/
│   └── environments/
├── .specify/                     # Spec Kit (features activas + history)
├── docs/                         # Documentación canónica
├── data/                         # Datasets locales (no secretos)
├── compose.yml                   # Compose canónico app (backend+frontend)
├── Makefile
└── README.md
```

## Responsabilidades

| Dominio | Rol |
|---------|-----|
| `apps/backend/` | API FastAPI |
| `apps/frontend/` | SPA Angular |
| `analytics/elt/` | ELT canónico |
| `infrastructure/airflow/` | Orquestación Airflow (metadata Postgres; no DuckDB de negocio) |
| `.specify/` | Constitución, features, history |
| `docs/` | Documentación; verdad en `docs/STATUS.md` |
| `compose.yml` | `docker compose up --build` (solo app) |

## Entradas

| Acción | Comando / doc |
|--------|----------------|
| Arranque | [../QUICKSTART.md](../QUICKSTART.md) |
| Docker app | `docker compose up --build` / `make up` |
| ELT CLI | `make pipeline` |
| Airflow ELT | `make airflow-up` / `make airflow-trigger` (tras detener app) |
| Estado producto | [../STATUS.md](../STATUS.md) |
| Specs históricas | [../../.specify/history/README.md](../../.specify/history/README.md) |
