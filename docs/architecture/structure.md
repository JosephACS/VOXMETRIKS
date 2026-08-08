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
│   ├── pocketbase/
│   └── environments/
├── .specify/                     # Spec Kit + history + features 045–047
├── docs/                         # Documentación canónica
├── data/                         # Datasets locales (no secretos)
├── compose.yml                   # Compose canónico
├── Makefile
└── README.md
```

## Responsabilidades

| Dominio | Rol |
|---------|-----|
| `apps/backend/` | API FastAPI |
| `apps/frontend/` | SPA Angular |
| `analytics/elt/` | ELT canónico |
| `.specify/` | Constitución, features cerradas, history |
| `docs/` | Documentación; verdad en `docs/STATUS.md` |
| `compose.yml` | `docker compose up --build` |

## Entradas

| Acción | Comando / doc |
|--------|----------------|
| Arranque | [../QUICKSTART.md](../QUICKSTART.md) |
| Docker | `docker compose up --build` / `make up` |
| ELT | `make pipeline` |
| Estado producto | [../STATUS.md](../STATUS.md) |
| Specs históricas | [../../.specify/history/README.md](../../.specify/history/README.md) |
