# Voxmetriks

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Angular 21](https://img.shields.io/badge/Angular-21-DD0031?logo=angular)](https://angular.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1-yellow)](https://duckdb.org)

**Plataforma de catálogo musical + analytics** — SPA Angular, API FastAPI y warehouse DuckDB (Medallion ELT).

**Estado:** demo / beta controlada (Release Candidate documental). No es un servicio de streaming con licencia comercial propia; la reproducción usa YouTube + Audius + audio demo.

Tras **spec 014** (estabilización): monorepo `apps/` + `analytics/elt` canónico; dominios técnicos `identity` / `catalog` / `engagement` / `analytics` / `ai` / `platform` (con adaptadores legacy).

**Capa empresarial (specs 016–028):** implementada con deuda aceptada — **024** Executive Reporting · **025** Customer Success & Support · cierre **028** → `ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT`.
**Suscripciones personales B2C (spec 029):** Free / Premium Individual / Duo / Familiar — `CLOSED_WITH_ACCEPTED_DEBT`. Separadas de planes empresariales.
Cuentas demo locales: seed opt-in (`DEMO_ACCOUNT_PASSWORD` / `.env.example`). Detalle de estado: [`docs/STATUS.md`](docs/STATUS.md).
Royalties/Payouts: **OUT_OF_SCOPE** (simulado). Specs históricas: [`.specify/history/`](.specify/history/README.md).

---

## Arquitectura (resumen)

```mermaid
flowchart LR
    FE[Angular SPA] --> API[FastAPI]
    API --> DB[(DuckDB)]
    PB[PocketBase] --> ELT[analytics/elt]
    ELT --> DB
```

| Ruta | Rol | Estado |
|------|-----|--------|
| `apps/frontend` | SPA Angular | **Implementado** |
| `apps/backend` | API FastAPI | **Implementado** |
| `analytics/elt` | Pipeline ELT canónico | **Implementado** |
| `apps/backend/app/etl` | Refresh runtime / tests | **Parcial** (adaptador; no rebuild completo) |
| `playback-core` | Dirección futura del player | **Parcial** / propuesto V2 |
| Organizations / CRM / billing / subscriptions | 016–019 | **Implementado** (MOCK payment; deuda aceptada) |
| Artists / catalog-rights / campaigns / biz-analytics | 020–023 | **Implementado** |
| Compliance / platform-ops | 026–027 | **Implementado** (integraciones MOCK) |
| Executive Reporting / Decisions | 024 | **IMPLEMENTED** (`/api/v1/reports`, `/business-decisions`) |
| Customer Success / Support | 025 | **IMPLEMENTED** (`/customer-success`, `/support`) |
| Royalties / Payouts | — | **OUT_OF_SCOPE** (futuro; no son 024/025) |

Detalle: [docs/STATUS.md](docs/STATUS.md) · Specs históricas: [.specify/history/](.specify/history/README.md) · ELT: [docs/architecture/elt.md](docs/architecture/elt.md)

---

## Cómo ejecutar

```bash
# Dependencias
make install
cd apps/frontend && npm install && cd ../..

# Warehouse (canónico)
make pipeline
# o: python analytics/elt/pipelines/elt_pipeline.py

# API local
make dev
# o: cd apps/backend && uvicorn app.main:app --reload --port 8000

# SPA local
cd apps/frontend && npm start
```

### Docker (comando oficial)

Stack canónico en la raíz (`compose.yml` + `infrastructure/docker/Dockerfile` para backend/ELT + `apps/frontend/Dockerfile`):

```bash
docker compose up --build
```

Equivalente: `make up`. Frontend en `:8080`, API en `:8000` (diagnóstico; el navegador usa Nginx `/api/`).

Guía completa: [docs/QUICKSTART.md](docs/QUICKSTART.md)

### Credenciales demo (solo development)

| Usuario | Password | Rol |
|---------|----------|-----|
| `demo` | `demo123` | user |
| `admin` | `admin123` | admin |

---

## Tests

```bash
# Backend
cd apps/backend && python -m pytest -q

# Frontend
cd apps/frontend && npm test && npm run lint && npm run build
```

Playwright (`automation/playwright`) y Docker Compose son **opcionales**; no asumir verdes si no se ejecutaron en el entorno.

---

## Specs SDD

Especificaciones: [.specify/history/](.specify/history/README.md)
Spec de estabilización: `.specify/history/014-repository-stabilization-domain-foundation/`

---

## Documentación

**Índice:** [docs/README.md](docs/README.md)

| Documento | Enlace |
|-----------|--------|
| Quickstart | [QUICKSTART.md](docs/QUICKSTART.md) |
| Estado de producto | [STATUS.md](docs/STATUS.md) |
| Modelo de negocio | [BUSINESS-MODEL.md](docs/product/BUSINESS-MODEL.md) |
| API | [api.md](docs/api/api.md) |
| Seguridad | [security.md](docs/security/security.md) |
