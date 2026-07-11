# Informe de migración Enterprise Monorepo

**Fecha:** 2026-07-05  
**Objetivo:** Reorganización física por dominios de responsabilidad, sin cambiar lógica de negocio, APIs ni imports de dominio.

---

## 1. Estructura final (raíz limpia)

```
voxmetriks/
├── apps/                    # Aplicaciones
│   ├── backend/             # FastAPI
│   └── frontend/            # Angular 21
├── analytics/               # Ingeniería de datos
│   └── elt/                 # Pipeline Medallion
├── automation/              # Automatización
│   ├── scripts/             # Ops, smoke, warehouse
│   ├── e2e/                 # Tests Playwright
│   ├── specs/               # SDD 001–013
│   └── playwright/          # Config npm Playwright
├── infrastructure/          # Infraestructura
│   ├── docker/              # Dockerfile, compose, .dockerignore
│   ├── pocketbase/          # Dataset cloud
│   ├── hooks/               # Git hooks (.githooks)
│   └── environments/        # .env.example
├── docs/                    # Documentación por categoría
├── data/                    # Datasets Medallion (solo datos)
├── archive/                 # Histórico + generated/
├── Makefile                 # Delega → infrastructure/Makefile
├── package.json             # Delega e2e → automation/playwright
├── QUICKSTART.md            # Redirect → docs/quickstart.md
└── README.md
```

**Elementos en raíz (visibles):** 7 dominios + 4 archivos de entrada.  
**Ocultos / tooling:** `.cursor/`, `.specify/`, `.vscode/`, `.env`, `.gitignore`  
**Gitignored locales:** `node_modules/`, `venv/`

---

## 2. Directorios movidos

| Origen (raíz) | Destino | Razón |
|---------------|---------|-------|
| `backend/` | `apps/backend/` | Separar aplicaciones |
| `frontend/` | `apps/frontend/` | Separar aplicaciones |
| `elt/` | `analytics/elt/` | Dominio de ingeniería de datos |
| `scripts/` | `automation/scripts/` | Herramientas de automatización |
| `e2e/` | `automation/e2e/` | Tests E2E |
| `specs/` | `automation/specs/` | Especificaciones SDD |
| `pocketbase/` | `infrastructure/pocketbase/` | Infraestructura |
| `.githooks/` | `infrastructure/hooks/` | Git hooks |
| `Dockerfile` | `infrastructure/docker/Dockerfile` | Infra Docker |
| `docker-compose.yml` | `infrastructure/docker/docker-compose.yml` | Orquestación |
| `.dockerignore` | `infrastructure/docker/.dockerignore` | Build context |
| `.env.example` | `infrastructure/environments/.env.example` | Plantilla de entorno |
| `package.json` (e2e) | `automation/playwright/package.json` | Config Playwright |
| `package-lock.json` | `automation/playwright/package-lock.json` | Lockfile E2E |
| `playwright.config.ts` | `automation/playwright/playwright.config.ts` | Config Playwright |
| `Makefile` | `infrastructure/Makefile` (+ stub raíz) | Comandos dev/ops |

---

## 3. Documentación reorganizada (21 archivos)

| Origen | Destino |
|--------|---------|
| `docs/01-introduction/quickstart.md` | `docs/quickstart.md` |
| `docs/01-introduction/faq.md` | `docs/faq.md` |
| `docs/01-introduction/contributing.md` | `docs/contributing.md` |
| `docs/01-introduction/windows-setup.md` | `docs/deployment/windows-setup.md` |
| `docs/02-architecture/architecture.md` | `docs/architecture/architecture.md` |
| `docs/02-architecture/structure.md` | `docs/architecture/structure.md` |
| `docs/03-database/database.md` | `docs/database/database.md` |
| `docs/04-backend/backend.md` | `docs/backend/backend.md` |
| `docs/05-frontend/frontend.md` | `docs/frontend/frontend.md` |
| `docs/06-elt/elt.md` | `docs/architecture/elt.md` |
| `docs/07-api/api.md` | `docs/api/api.md` |
| `docs/08-testing/testing.md` | `docs/testing/testing.md` |
| `docs/09-deployment/deployment.md` | `docs/deployment/deployment.md` |
| `docs/10-security/security.md` | `docs/security/security.md` |
| `docs/11-performance/performance.md` | `docs/performance/performance.md` |
| `docs/12-audit/*` | `docs/archive/*` |
| `docs/13-presentation/*` | `docs/presentation/*` |
| `docs/14-roadmap/*` | `docs/roadmap/*` |
| `docs/15-portfolio/*` | `docs/portfolio/*` |

Carpetas `docs/` por categoría: `architecture/`, `backend/`, `frontend/`, `database/`, `api/`, `deployment/`, `testing/`, `security/`, `performance/`, `uml/`, `screenshots/`, `presentation/`, `roadmap/`, `portfolio/`, `archive/`.

---

## 4. Archivos renombrados

Ningún archivo de código renombrado. Solo reubicación de rutas.

---

## 5. Archivos eliminados (temporales)

| Archivo | Razón |
|---------|-------|
| `.pytest_cache/` (raíz) | Caché de pytest, regenerable |
| `backend/` (carpeta vacía post-migración) | Residuo tras mover a `apps/backend/` |

**No se eliminó código, documentación útil ni configuraciones necesarias.**

---

## 6. Rutas actualizadas (configuración / resolución de paths)

### Infraestructura
- `infrastructure/docker/docker-compose.yml` — `context: ../..`, volúmenes y `env_file` relativos a raíz
- `infrastructure/docker/Dockerfile` — `COPY apps/backend/`, `COPY analytics/elt/`
- `infrastructure/Makefile` — `ROOT`, `PYTHONPATH`, compose con `--project-directory`
- `Makefile` (raíz) — delegación a `infrastructure/Makefile`
- `package.json` (raíz) — delegación e2e a `automation/playwright`

### Playwright
- `automation/playwright/playwright.config.ts` — imports `../e2e/*`, `cwd: ../../apps/backend|frontend`, reportes en `archive/generated/`
- `automation/playwright/package.json` — `--prefix` hacia apps

### Backend (solo resolución de rutas, sin lógica)
- `apps/backend/app/core/config.py` — `_find_project_root()` dinámico; `.env` desde múltiples ubicaciones
- `apps/backend/app/packages/analytics/services/paths.py` — `get_settings().data_root`
- `analytics/elt/pipelines/*.py` — `parents[3]` para repo root
- `apps/backend/tests/test_enterprise_api.py` — depth paths

### Automation scripts
- `automation/scripts/*.py` — `ROOT` depth + `apps/backend` + PYTHONPATH `analytics/`

### Cursor / Spec Kit
- `.cursor/rules/specify-rules.mdc` → `automation/specs/013-academic-defense-deliverables/plan.md`
- `.specify/feature.json` → `automation/specs/013-academic-defense-deliverables`

### Documentación (correcciones post-migración)
- `docs/testing/testing.md` — `apps/backend/.env.e2e.example`
- `docs/deployment/windows-setup.md` — `apps/backend/requirements.txt`
- `docs/portfolio/portfolio.md` — enlace a `docs/contributing.md`
- `docs/architecture/structure.md` — árbol enterprise actualizado
- `README.md` — referencia `automation/specs/`

### Gitignore
- `apps/frontend/dist/`, `archive/generated/playwright-report/`, `archive/generated/test-results/`

**Lógica de negocio, APIs REST, imports de dominio Python/TypeScript: sin cambios.**

---

## 7. Artefactos generados

Destino configurado: `archive/generated/`

| Artefacto | Ubicación |
|-----------|-----------|
| Playwright HTML report | `archive/generated/playwright-report/` |
| Playwright test-results | `archive/generated/test-results/` |
| Frontend build (local) | `apps/frontend/dist/` (gitignored) |

---

## 8. Validación ejecutada

| Componente | Resultado |
|------------|-----------|
| Backend import | `from app.main import app` → OK |
| Frontend build | `npm run build` → OK (budget warnings preexistentes) |
| Playwright config | `npx playwright test --list` → 45 tests detectados |
| pytest (suite completa) | 108 tests, 5 fallos intermitentes por orden/estado compartido (pasan individualmente); no relacionados con paths |
| `make` en Windows | No disponible en PATH del entorno de prueba; usar `infrastructure/Makefile` directamente o instalar make |

### Comandos post-migración

```bash
# Backend
cd apps/backend && pytest tests/

# Frontend
cd apps/frontend && npm start

# E2E (desde raíz)
npm run e2e

# Docker (con make instalado)
make up

# ELT
python analytics/elt/pipelines/elt_pipeline.py
```

**PYTHONPATH requerido:** `apps/backend` + raíz + `analytics`

---

## 9. Script de migración

`automation/scripts/dev/enterprise_monorepo_migrate.py` — idempotente; puede re-ejecutarse para verificar estado.

---

## 10. Notas

- El contenedor Docker mantiene rutas internas `/app/backend` y `/app/elt` (sin cambios en runtime).
- `apps/backend/Makefile` y `apps/backend/Dockerfile` se conservan para desarrollo standalone local.
- `node_modules/` y `venv/` permanecen en raíz (gitignored); son dependencias locales, no código del proyecto.
