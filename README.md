# Voxmetriks

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Angular 21](https://img.shields.io/badge/Angular-21-DD0031?logo=angular)](https://angular.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1-yellow)](https://duckdb.org)

**Plataforma de catálogo musical + analytics** — SPA Angular, API FastAPI y warehouse DuckDB (Medallion ELT).

**Estado:** demo / beta controlada (Release Candidate documental). No es un servicio de streaming con licencia comercial propia; la reproducción usa YouTube + Audius + audio demo.

Tras **spec 014** (estabilización): monorepo `apps/` + `analytics/elt` canónico; dominios técnicos `identity` / `catalog` / `engagement` / `analytics` / `ai` / `platform` (con adaptadores legacy).

**Capa empresarial (specs 016–023, 026–027):** implementada con deuda aceptada — cierre documental **spec 028** → `ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT`. Detalle: [automation/specs/028-enterprise-integration-and-final-validation/](automation/specs/028-enterprise-integration-and-final-validation/).

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
| Royalties / Payouts | 024–025 | **No presentes** en este workspace |
| Customer Success / Support / Exec report | 015 diseño | **Diferido** (028 no autoriza build) |

Detalle: [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) · Empresa: [automation/specs/028-enterprise-integration-and-final-validation/architecture-as-implemented.md](automation/specs/028-enterprise-integration-and-final-validation/architecture-as-implemented.md) · ELT: [docs/architecture/elt.md](docs/architecture/elt.md)

---

## Cómo ejecutar

```bash
# Dependencias
make install
cd apps/frontend && npm install && cd ../..

# Warehouse (canónico)
make pipeline
# o: python analytics/elt/pipelines/elt_pipeline.py

# API
make dev
# o: cd apps/backend && uvicorn app.main:app --reload --port 8000

# SPA
cd apps/frontend && npm start
```

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

Especificaciones: [automation/specs/](automation/specs/README.md)  
Spec de estabilización: `automation/specs/014-repository-stabilization-domain-foundation/`

---

## Documentación

**Índice:** [docs/README.md](docs/README.md)

| Documento | Enlace |
|-----------|--------|
| Quickstart | [QUICKSTART.md](docs/QUICKSTART.md) |
| Features | [PRODUCT_FEATURES.md](docs/PRODUCT_FEATURES.md) |
| Release Notes | [RELEASE_NOTES.md](docs/RELEASE_NOTES.md) |
| API | [api.md](docs/api/api.md) |
| Seguridad | [security.md](docs/security/security.md) |
