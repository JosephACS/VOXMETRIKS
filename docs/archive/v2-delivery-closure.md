# VOXMETRIK V2 — Cierre de entrega

**Fecha:** 2026-07-05  
**Estado E2E:** 45/45 passed, 0 failed, 0 flaky (~41 s)

---

## 1. Regeneración de actividad sintética

### Ejecutado

- Regeneración completa sobre copia de warehouse (`data/warehouse/voxmetrik_regen.duckdb`) con `target_total=950_000` (equivalente a POST `/api/v1/stats/synthetic` desde `/elt-pipeline`).
- **Corrección aplicada:** el endpoint `/stats/synthetic` usaba conexión DuckDB **solo lectura**; ahora usa `get_write_conn` (requiere reiniciar el backend para cargar el fix).

### Métricas tras regenerar (warehouse `voxmetrik_regen.duckdb`)

| Métrica | Valor |
|---------|--------|
| Eventos totales | 950 000 |
| Filas `fact_streaming` | 617 500 |
| Días en `agg_daily_streams` (últimos 90) | suma 617 500 |
| Variación diaria (`total_streams`/día) | min 3 528 · max 11 229 · **15 valores distintos** |
| Horas pico (`fact_streaming` por hora) | min 8 233 · max 80 275 · **24 buckets** |
| `agg_tracks_populares` | 89 740 filas |
| Dispositivos | mobile / desktop / web / tablet / smart_tv con pesos distintos |

### Promover datos al warehouse activo

El backend en `:8000` mantiene el archivo DuckDB bloqueado. Para que la UI en `:4200` use los datos regenerados:

```powershell
# 1. Detener uvicorn en :8000
# 2. Promover warehouse
Copy-Item -Force data/warehouse/voxmetrik_regen.duckdb data/warehouse/voxmetrik.duckdb
# 3. Reiniciar backend (sin variables E2E)
cd apps/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
# 4. (Opcional) Repetir desde UI: login admin → /elt-pipeline → ejecutar pipeline
```

### Verificación manual de los 4 módulos (post-promoción)

| Módulo | Ruta | Qué confirmar |
|--------|------|----------------|
| Centro analítico | `/dashboard` | KPIs numéricos; gráfico de tendencia con variación (no línea plana); tablas inferiores con filas |
| Analítica de streaming | `/insights/analytics` | Serie temporal con picos/valles; barras de horas pico desiguales |
| Canciones destacadas | `/insights/tracks` | Tabla con filas (`data-testid="table-row"`); paginador > 0 |
| Comparativas | `/comparatives` | Heatmap con 3 filas: Popularidad, Energía, Canciones |

---

## 2. Variables de entorno E2E (aisladas)

| Variable | Valor E2E | Dónde se aplica | ¿En `.env` por defecto? |
|----------|-----------|-----------------|-------------------------|
| `E2E` | `1` | `npm run e2e:backend`, `playwright.config.ts` webServer | **No** |
| `GLOBAL_RATE_LIMIT` | `0` | Scripts E2E / pytest `conftest.py` | **No** (default prod/dev: **120** en `apps/backend/.env.example`) |
| `AUTH_RATE_LIMIT` | `0` | Idem | **No** (default: **20**) |

### Salvaguardas en código

- `apps/backend/.env.e2e.example` — plantilla exclusiva para runs Playwright (no cargar en dev/prod).
- `Settings.effective_global_rate_limit` / `effective_auth_rate_limit` — si `GLOBAL_RATE_LIMIT=0` o `AUTH_RATE_LIMIT=0` **sin** `E2E=1` ni pytest, se restauran los defaults (120 / 20).
- `playwright.config.ts` — webServer desactivado por defecto; solo arranca servidores managed con `PLAYWRIGHT_USE_WEBSERVER=1`.

**Desarrollo y producción:** usar `apps/backend/.env.example` (rate limits 20/120). No copiar `.env.e2e.example` al `.env` principal.

---

## 3. `data-testid` (integración limpia)

| Componente | Atributo | Notas |
|------------|----------|-------|
| `dashboard-layout` | `app-shell`, `app-sidebar-nav`, `user-menu-btn`, `logout-btn` | Sin cambios de clases CSS; `aria-label` existentes intactos |
| `player-bar` | `player-bar`, `player-play-btn` | Sigue en `<footer>` semántico; botón play conserva `aria-label` i18n |
| `search` | `search-input` | Atributo en `<input type="search">` nativo |
| `table-widget` | `table-widget`, `table-row` | En `<section>` y `<tr mat-row>`; sin impacto visual |

Los testids son hooks de prueba; no sustituyen roles ARIA ni headings.

---

## 4. Resumen de correcciones incluidas en el cierre

- **Backend:** `get_write_conn` en POST `/stats/synthetic`; guard de rate-limit E2E; fix SQL `build_agg_tracks_populares` (sin columna `engagement_score` inexistente).
- **Datos:** distribución diaria con variación real en `facts.py` (buckets 30+30+30 días con hash).
- **Frontend:** `MatTableDataSource` en `table-widget` para filas async.
- **E2E:** 45 tests; login único vía `global-setup.ts`; proyectos `auth` / `authenticated` separados.

---

## 5. Comandos de referencia

```powershell
# E2E (servidores externos)
npm run e2e:backend   # E2E=1, rate limits 0
npm run e2e:frontend
npm run e2e           # Playwright, sin webServer managed

# Regeneración CLI (backend detenido)
python automation/scripts/generate_activity.py --target 950000
```

**Tarea de entrega:** completa, pendiente solo de promover `voxmetrik_regen.duckdb` y reiniciar backend `:8000` para ver los datos regenerados en la UI principal.
