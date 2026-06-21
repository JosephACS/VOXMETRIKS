# Voxmetriks

Plataforma de analítica musical sobre dataset Spotify: SPA Angular + API FastAPI + warehouse DuckDB (arquitectura Medallion).

**Documentación canónica:** este README es el único punto de entrada. El arranque operativo está en [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

---

## Qué es

| Capa | Tecnología | Ubicación |
|------|------------|-----------|
| Frontend | Angular 21 | `frontend/` |
| API | FastAPI 2.x | `backend/app/` |
| Warehouse | DuckDB (Gold + tablas app) | `data/warehouse/voxmetrik.duckdb` |
| ELT | Python (Bronze → Silver → Gold) | `elt/pipelines/elt_pipeline.py` |
| Specs SDD | Markdown 001–011 | `specs/` |

Principios de diseño: package-by-domain (P2), single warehouse authority (P4), ELT-before-API (P7). Ver [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

---

## Inicio rápido

```bash
# Ver guía completa paso a paso
docs/QUICKSTART.md
```

Resumen mínimo (local):

1. `pip install -r requirements.txt` y `pip install -r backend/requirements.txt`
2. `cp .env.example .env`
3. `python elt/pipelines/elt_pipeline.py`
4. `cd backend && uvicorn app.main:app --reload`
5. `cd frontend && npm install && npm start` → http://localhost:4200

Credenciales demo (seed automático): `demo` / `demo123`. Engineer (pipeline/explorer): `admin` / `admin123`.

---

## Estructura del repositorio

```
voxmetriks/
├── frontend/              # SPA Angular (PKG-01..07)
├── backend/
│   ├── app/               # FastAPI — main.py, packages/
│   └── tests/             # pytest (health, login, playlists, favorites)
├── elt/                   # Extract / transform / pipelines
├── data/warehouse/        # DuckDB canónico (generado por ELT)
├── specs/                 # Specs operativas 001–011 + trazabilidad
├── docs/
│   ├── QUICKSTART.md      # ← guía única de arranque
│   └── uml/               # Diagramas PlantUML
├── docker-compose.yml     # pipeline (job) → api → pocketbase
└── scripts/               # validate_warehouse.py, analyze_warehouse.py
```

---

## API y salud

| Recurso | URL |
|---------|-----|
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| API v1 | http://localhost:8000/api/v1/… |

Prefijo REST: `/api/v1`. Autenticación: header `Authorization: Bearer <token>` (login en `/api/v1/users/login`).

---

## Specs y trazabilidad

| Documento | Descripción |
|-----------|-------------|
| [`specs/README.md`](specs/README.md) | Índice specs 001–011 |
| [`specs/TRACEABILITY-MASTER.md`](specs/TRACEABILITY-MASTER.md) | Matriz CU→FR→Impl v2.0 (248 filas) |
| [`specs/DELIVERY-VERIFICATION-CHECKLIST.md`](specs/DELIVERY-VERIFICATION-CHECKLIST.md) | Verificación pre-entrega (Bloque 5) |
| [`specs/TRACEABILITY-COVERAGE-REPORT.md`](specs/TRACEABILITY-COVERAGE-REPORT.md) | Cobertura trazabilidad v2.0 |
| [`docs/uml/`](docs/uml/) | Casos de uso, componentes, arquitectura, flujo ELT |

Auditorías de soporte: `specs/OPERATIVE-COMPLETENESS-AUDIT.md`, `specs/SPEC-008-011-EVIDENCE-AUDIT.md`.

---

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/test_api.py -v
```

12 tests mínimos: health, login, playlists, favorites.

---

## Docker (opcional)

```bash
docker compose up --build
```

El servicio `pipeline` ejecuta el ELT una vez; `api` arranca cuando el pipeline termina con éxito (P7). Ver `docker-compose.yml`.

---

## Licencia

Proyecto académico Voxmetriks — uso según indicaciones del curso o cliente.
