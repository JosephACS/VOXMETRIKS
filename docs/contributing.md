# Contributing — Guía de contribución

Gracias por interesar en VOXMETRIK_V2. Este proyecto sigue principios Spec-Driven Development (SDD) documentados en `specs/` y `.specify/memory/constitution.md`.

## Cómo contribuir

1. **Fork** el repositorio
2. **Crea una rama** descriptiva: `feat/dashboard-cache`, `fix/login-rate-limit`
3. **Implementa** siguiendo las convenciones existentes
4. **Ejecuta tests:** `cd apps/backend && pytest tests/ -q`
5. **Lint:** `ruff check backend/app`
6. **Abre Pull Request** con descripción clara

## Convenciones de código

### Python (backend)

- PEP 8 via **ruff**
- Type hints en funciones públicas
- Docstrings solo para lógica no obvia
- Patrón: Route → Service → Repository
- SQL en `app/sql/*.sql`, no inline en routes
- Config via `get_settings()`, nada hardcodeado

### TypeScript (frontend)

- Standalone components
- `OnPush` en componentes shared
- Servicios `providedIn: 'root'`
- Unsubscribe con `takeUntilDestroyed`
- i18n via `I18nService`

### Commits

Formato recomendado:
```
tipo(alcance): descripción breve

- detalle opcional
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Estructura de specs

Antes de features nuevas, consultar o crear spec en `specs/NNN-feature-name/`:
- `spec.md` — requisitos
- `plan.md` — diseño
- `tasks.md` — tareas

## Tests obligatorios

- Nuevo endpoint → test en `tests/test_*_api.py`
- Nuevo servicio crítico → unit test
- Fix bug → test de regresión

## No hacer

- ❌ Commitear `.env` o `*.duckdb`
- ❌ Cambiar nombres de tablas warehouse sin migración
- ❌ Agregar dependencias sin justificación en PR
- ❌ Romper endpoints existentes sin versionado

## Reportar bugs

Incluir:
1. Pasos para reproducir
2. Comportamiento esperado vs actual
3. Logs relevantes (`logs/errors.log`)
4. Versión Python/Node

## Contacto

Proyecto académico Voxmetriks — consultar indicaciones del curso o maintainer del repo.
