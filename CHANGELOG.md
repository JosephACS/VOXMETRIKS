# Changelog

All notable changes to VOXMETRIKS are documented in this file.

## Enterprise Audit Pass — 2026-07-05

Cierre controlado Fase 5: correcciones mínimas para demo estable derivadas de auditorías Fases 1–4.

### Navegación

- Home **Descubrir → Ver todo** ahora abre `/insights/tracks` (ranking destacadas) en lugar del catálogo CRUD `/tracks`.
- Banda analítica **Ver más** apunta a `/dashboard` (centro enterprise) en lugar de `/analytics` legacy.

### Paginación

- Infinite scroll en `/insights/tracks`: deduplicación por `id_track` al cargar más páginas.
- Detalle de artista: **Cargar más canciones** deduplica por `id_track`.

### UX

- Eliminados KPI trends ficticios (`KPI_TRENDS` +6%, +8%, …).
- Trend en KPI “Tracks” solo cuando hay datos reales de crecimiento de catálogo.
- Eliminada tarjeta KPI “Likes” duplicada (mismo valor que Favoritos).
- Error parcial en detalle artista vía i18n (sin `console.error`).

### QA

- pytest suite completa: **110 passed, 1 skipped**.
- Test DB ampliada: `fact_streaming` con `skipped`/`fecha_evento`, `agg_daily_streams` con `skip_count`.
- Playwright `analytics-modules.spec.ts`: alineado con media cards en `/insights/tracks`; dashboard tolera empty state.

### Backend

- Compatibilidad schema DuckDB: queries aceptan `skip_rate` o `skip_count` en `agg_daily_streams`.
- Fix typo `id_genre` → `id_genero` en actualización de tracks.
- Top tracks fallback: `COUNT(*)` en lugar de columna inexistente `streams`.
- `/stats/synthetic`: autenticación evaluada antes de abrir conexión write (401/403 correctos).

### Frontend

- `data-testid="featured-track-card"` en ranking destacadas.
- Build producción Angular sin errores (warnings de budget existentes).

### Documentación

- Nuevo [docs/AUDIT_REPORT_ENTERPRISE.md](docs/AUDIT_REPORT_ENTERPRISE.md) con hallazgos, correcciones y validaciones Fase 5.
