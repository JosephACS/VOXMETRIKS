# Reorganización Enterprise — Informe

**Fecha:** 2026-07-05  
**Alcance:** Solo documentación y estructura de carpetas. **Sin cambios en código de aplicación, APIs ni rutas runtime.**

---

## 1. Carpetas creadas

### Documentación numerada (`docs/`)

| Carpeta | Propósito |
|---------|-----------|
| `docs/01-introduction/` | Arranque, FAQ, contribución, Windows |
| `docs/02-architecture/` | Arquitectura y mapa del repo |
| `docs/03-database/` | Catálogo DuckDB |
| `docs/04-backend/` | FastAPI |
| `docs/05-frontend/` | Angular |
| `docs/06-elt/` | Pipeline Medallion (antes `ETL.md`) |
| `docs/07-api/` | Referencia REST |
| `docs/08-testing/` | pytest + Playwright |
| `docs/09-deployment/` | Docker y producción |
| `docs/10-security/` | Seguridad |
| `docs/11-performance/` | Rendimiento |
| `docs/archive/` | Auditoría y cierre V2 |
| `docs/13-presentation/` | Defensa académica |
| `docs/14-roadmap/` | Hoja de ruta |
| `docs/15-portfolio/` | Portafolio |

### UML (`docs/uml/`)

| Carpeta | Contenido |
|---------|-----------|
| `use-cases/` | Casos de uso + `packages/uc-*.puml` |
| `components/` | Diagramas de componentes |
| `architecture/` | Arquitectura de despliegue |
| `elt/` | Flujo ELT |
| `classes/` | Clases core y warehouse |
| `sequence/` | Secuencias |
| `context/` | Paquetes / contexto |
| `_rendered/{use-cases,classes,sequence}/` | PNG exportados |

### Screenshots (`docs/screenshots/`)

`apps/frontend/`, `apps/backend/`, `dashboard/`, `elt/`, `database/`, `api/`

---

## 2. Archivos movidos (20 documentos)

| Origen | Destino |
|--------|---------|
| `docs/QUICKSTART.md` | `docs/quickstart.md` |
| `docs/FAQ.md` | `docs/01-introduction/faq.md` |
| `docs/CONTRIBUTING.md` | `docs/01-introduction/contributing.md` |
| `docs/WINDOWS_SETUP.md` | `docs/01-introduction/windows-setup.md` |
| `docs/ARCHITECTURE.md` | `docs/architecture/architecture.md` |
| `docs/STRUCTURE.md` | `docs/architecture/structure.md` |
| `docs/DATABASE.md` | `docs/database/database.md` |
| `docs/BACKEND.md` | `docs/backend/backend.md` |
| `docs/FRONTEND.md` | `docs/frontend/frontend.md` |
| `docs/ETL.md` | `docs/architecture/elt.md` |
| `docs/API.md` | `docs/api/api.md` |
| `docs/TESTING.md` | `docs/testing/testing.md` |
| `docs/DEPLOYMENT.md` | `docs/deployment/deployment.md` |
| `docs/SECURITY.md` | `docs/security/security.md` |
| `docs/PERFORMANCE.md` | `docs/performance/performance.md` |
| `docs/AUDIT_REPORT.md` | `docs/archive/audit-report.md` |
| `docs/V2-DELIVERY-CLOSURE.md` | `docs/archive/v2-delivery-closure.md` |
| `docs/PRESENTATION_GUIDE.md` | `docs/presentation/presentation-guide.md` |
| `docs/ROADMAP.md` | `docs/roadmap/roadmap.md` |
| `docs/PORTFOLIO.md` | `docs/portfolio/portfolio.md` |

**UML:** 14 diagramas raíz + 17 en `packages/` + 19 PNG reclasificados → ver `scripts/dev/reorganize_enterprise_docs.py`.

---

## 3. Archivos renombrados (nomenclatura)

| Antes | Después | Notas |
|-------|---------|-------|
| `ETL.md` | `elt.md` | Terminología ELT en documentación |
| `ARCHITECTURE.md` | `architecture.md` | kebab-case |
| `STRUCTURE.md` | `structure.md` | idem |
| `API.md` | `api.md` | idem |
| *(todos los .md planos)* | `lowercase.md` | Estilo consistente |

Código y carpetas `apps/backend/app/etl/` **no modificados** (módulo interno existente).

---

## 4. Archivos eliminados

**Ningún archivo de código ni documentación con contenido fue eliminado.**

- Duplicados planos en `docs/` eliminados implícitamente al **mover** (solo queda `docs/README.md` en la raíz de docs).
- `docs/uml/packages/` vacía → eliminada tras mover a `use-cases/packages/`.
- No se eliminaron specs, archive histórico ni código backend/frontend.

---

## 5. Archivos actualizados (enlaces y entradas)

| Archivo | Cambio |
|---------|--------|
| `README.md` (raíz) | Reducido a descripción, arquitectura, stack, run, enlace a docs |
| `docs/README.md` | Índice enterprise por secciones |
| `QUICKSTART.md` (raíz) | Redirect a `docs/quickstart.md` |
| `docs/uml/README.md` | Estructura por categoría |
| `docs/screenshots/README.md` | Subcarpetas por módulo |
| `docs/architecture/structure.md` | Árbol docs numerado |
| 30+ `.md` en repo | Enlaces internos actualizados automáticamente |
| 17 docs | Enlaces relativos cruzados corregidos |

---

## 6. Justificación por área

| Decisión | Por qué |
|----------|---------|
| Carpetas `01-`…`15-` | Navegación predecible tipo enterprise; orden lógico onboarding → ops |
| `elt.md` vs `ETL.md` | Alineación con arquitectura ELT real (`elt/`) sin tocar código |
| UML por categoría | Facilita mantenimiento y render selectivo |
| README corto | Una sola puerta de entrada; detalle en `/docs` |
| `QUICKSTART.md` raíz | Compatibilidad con bookmarks antiguos |
| Sin mover `specs/` | SDD activo; fuera del alcance de docs técnicas |
| Sin mover `apps/backend/`/`apps/frontend/` | Evitar romper imports y rutas |

---

## 7. Verificación de no-regresión

| Área | Estado |
|------|--------|
| Código backend (`apps/backend/app/`) | **Sin cambios** |
| Código frontend (`frontend/src/`) | **Sin cambios** |
| Rutas API | **Sin cambios** |
| `infrastructure/docker/docker-compose.yml` / `Dockerfile` | **Sin cambios** |
| `Makefile` / `package.json` scripts | **Sin cambios** |
| `e2e/` Playwright | **Sin cambios** |
| `elt/` pipeline | **Sin cambios** |
| `specs/` SDD | **Sin cambios** (solo enlaces en markdown) |

---

## 8. Script reutilizable

`scripts/dev/reorganize_enterprise_docs.py` — automatiza movimientos y reemplazo de enlaces (uso puntual; ya ejecutado).

---

## 9. Árbol resumido (post-reorganización)

```
voxmetriks/
├── backend/          # FastAPI + tests
├── frontend/         # Angular SPA
├── elt/              # Pipeline Medallion
├── data/             # warehouse, bronze, silver, gold
├── docs/
│   ├── 01-introduction/ … 15-portfolio/
│   ├── uml/{use-cases,components,architecture,elt,classes,sequence,context,_rendered}
│   ├── screenshots/{frontend,backend,dashboard,elt,database,api}
│   └── archive/
├── e2e/              # Playwright
├── pocketbase/
├── scripts/
├── specs/            # SDD 001–013
├── archive/          # Código histórico
├── infrastructure/docker/docker-compose.yml
├── Dockerfile
├── Makefile
├── package.json
└── README.md
```

---

**Confirmación:** esta reorganización afecta únicamente documentación, índices y estructura de carpetas de docs/UML/screenshots. **Ninguna funcionalidad del sistema fue modificada.**
