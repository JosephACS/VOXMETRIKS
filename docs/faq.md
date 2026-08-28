# FAQ — Preguntas frecuentes

## General

### ¿Qué es VOXMETRIK_V2?
Plataforma de streaming musical con analytics avanzado sobre dataset Spotify. Combina experiencia tipo Spotify (Angular) con warehouse analítico DuckDB y dashboards enterprise.

### ¿Es un clon de Spotify?
No. Es una **plataforma de demostración académica/profesional** que replica patrones UX de streaming y añade capa analítica Medallion no presente en Spotify consumer.

### ¿Usa machine learning?
El motor de recomendaciones es **heurístico y explicable** (scoring ponderado SQL). ML está planificado en v3.0 ([roadmap.md](roadmap/roadmap.md)).

---

## Técnicas

### ¿Por qué DuckDB y no PostgreSQL?
DuckDB es OLAP embebido: cero infraestructura, excelente para agregaciones analíticas locales, portable (un archivo). PostgreSQL sería mejor para OLTP multi-usuario concurrente, pero este proyecto prioriza **analytics sobre ~100k filas** sin ops overhead.

### ¿Por qué tablas AGG?
Pre-calculan métricas costosas (GROUP BY sobre facts). Dashboard responde en ms leyendo `agg_daily_streams` vs segundos escaneando `fact_streaming`. Patrón estándar en Snowflake/BigQuery (materialized views).

### ¿Por qué arquitectura Medallion?
Separa raw (inmutable), silver (limpio), gold (modelado). Permite reprocesar capas, auditar transformaciones y escalar el pipeline sin tocar la API.

### ¿Por qué FastAPI?
OpenAPI automático, async nativo, validación Pydantic, tipado, performance comparable a Node/Go. Ideal para APIs REST analíticas.

### ¿Por qué Angular?
Framework enterprise con DI, lazy loading, i18n, Material Design. Standalone components (v21) eliminan complejidad NgModule.

### ¿Cómo escala el sistema?
**Actual:** single-node, DuckDB local, cache in-process — apto demo/académico. No hay evidencia en este repo de capacidad concurrente medida ni SLA.
**Futuro (propuesto, no comprobado):** Redis cache, read replicas, warehouse cloud, orquestación — ver [roadmap.md](roadmap/roadmap.md).

### ¿Cómo migrar a Snowflake?
1. Export Parquet desde DuckDB gold tables
2. `COPY INTO` Snowflake external stage
3. Recrear dims/facts/agg como Snowflake tables
4. Cambiar `DuckDBClient` por `snowflake-connector` en repositories
5. Mantener misma interfaz Service/Repository

### ¿Cómo migrar a BigQuery?
Similar: export → GCS → BigQuery load job → dbt para transforms → API lee via BigQuery client.

### ¿Cómo agregar IA?
v3.0 roadmap (propuesto): embeddings, vector search, hybrid ranking — ver [roadmap.md](roadmap/roadmap.md). Estado vigente: [STATUS.md](STATUS.md).

---

## Operacionales

### ¿Dónde está el warehouse?
`data/warehouse/voxmetrik.duckdb` — generado por ELT, no versionado en git.

### ¿Cómo resetear datos?
```bash
rm data/warehouse/voxmetrik.duckdb
python analytics/elt/pipelines/elt_pipeline.py
```

### ¿Credenciales demo?
Primer acceso: registro en la UI o `python apps/backend/scripts/bootstrap_admin.py` (`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD`). Seeds DEV opcionales: ver `.env.development.example`.

### ¿Por qué no veo /docs en producción?
`ENVIRONMENT=production` desactiva Swagger por seguridad. Usar [api.md](api/api.md).

### ¿El frontend no conecta al backend?
Verificar CORS (`CORS_ORIGINS`), proxy nginx, y que API corre en `:8000`.

---

## Académicas

### ¿Qué specs cubre el proyecto?
Historial 001–031 (y cierre 045–047) en [`.specify/history/`](../.specify/history/README.md) y [`.specify/features/`](../.specify/features/). Estado de producto: [STATUS.md](STATUS.md).

### ¿Dónde están los diagramas UML?
`docs/uml/` — PlantUML retenido (casos de uso, componentes, secuencias, ELT).
