# Estructura del repositorio (Enterprise)

Mapa oficial del monorepo **Voxmetriks**.

```
voxmetriks/
├── apps/                         # Aplicaciones desplegables
│   ├── backend/                  # FastAPI — API REST
│   └── frontend/                 # Angular 21 — SPA
├── analytics/                    # Ingeniería de datos
│   └── elt/                      # Pipeline Medallion (PocketBase → DuckDB)
├── automation/                   # Herramientas de automatización
│   ├── scripts/                  # Ops, smoke, warehouse
│   ├── e2e/                      # Playwright E2E
│   ├── specs/                    # SDD 001–013
│   └── playwright/               # Config npm Playwright
├── infrastructure/               # Infraestructura y entorno
│   ├── docker/                   # Dockerfile, compose, .dockerignore
│   ├── pocketbase/               # Dataset cloud + migraciones
│   ├── hooks/                    # Git hooks
│   └── environments/             # .env.example
├── docs/                         # Documentación técnica
├── data/                         # Datasets Medallion (warehouse, bronze, …)
├── archive/                      # Histórico + generated/
├── Makefile                      # Delega a infrastructure/Makefile
├── package.json                  # Delega e2e a automation/playwright
└── README.md
```

## Responsabilidades

| Dominio | Rol |
|---------|-----|
| `apps/backend/` | API 93 endpoints, auth, recomendaciones, explorer |
| `apps/frontend/` | UI streaming + analytics hub (ECharts) |
| `analytics/elt/` | Ingesta batch PocketBase → Parquet → DuckDB |
| `apps/backend/app/etl/` | Builders incrementales al arrancar API |
| `data/` | Artefactos generados; catálogo fuente en PocketBase |
| `automation/scripts/` | Smoke tests, warehouse, actividad sintética |
| `automation/specs/` | Requisitos trazables CU→FR→CA |
| `infrastructure/` | Docker, PocketBase, variables de entorno |
| `archive/` | Código superseded; `archive/generated/` para artefactos E2E |

## Puntos de entrada

| Acción | Comando / doc |
|--------|----------------|
| Arranque | [quickstart.md](../quickstart.md) |
| Docker | `make up` |
| ELT completo | `make pipeline` |
| API dev | `make dev` |
| Tests backend | `make test` |
| E2E | `npm run e2e` (desde raíz) |
| Docs índice | [README.md](../README.md) |

## Convenciones

- **ELT** (Extract-Load-Transform): `analytics/elt/` + documentación
- **Imports Python `elt.*`**: requieren `PYTHONPATH` con raíz del repo + `analytics/` (`make` lo exporta)
- **Contenedor Docker**: rutas internas `/app/backend` y `/app/elt` (sin cambios)
- **No CSV en `data/`**: Bronze es cache Parquet desde PocketBase
