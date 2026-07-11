# Guía de presentación — Defensa académica

Documento de preparación para exposición oral, preguntas del tribunal y demo en vivo.

---

## 1. Elevator pitch (60 segundos)

> VOXMETRIK_V2 es una plataforma de streaming musical con capa analítica enterprise. El usuario escucha música, crea playlists y recibe recomendaciones; el analista explora un warehouse DuckDB con arquitectura Medallion que procesa ~100k eventos Spotify. El frontend Angular consume una API FastAPI con tres capas: rutas delgadas, servicios de negocio y repositorios SQL. Las métricas del dashboard leen tablas pre-agregadas, no facts crudos, garantizando respuesta sub-segundo.

---

## 2. Explicación de arquitectura (5 minutos)

### Capas

1. **Presentación** — Angular SPA, lazy loading, Material + ECharts
2. **API** — FastAPI, 93 endpoints, envelope JSON uniforme
3. **Negocio** — Services (analytics, tracks, recommendations)
4. **Datos** — Repositories → DuckDB (48 tablas, Medallion)
5. **ETL** — PocketBase → Bronze → Silver → Gold → Agg

Mostrar diagrama en [architecture.md](../02-architecture/architecture.md).

---

## 3. Decisiones técnicas — ¿Por qué?

### ¿Por qué FastAPI?
- Generación automática OpenAPI → documentación viva
- Validación Pydantic → menos bugs en runtime
- Async → preparado para I/O concurrente
- Ecosistema Python → ETL y API mismo lenguaje

### ¿Por qué Angular?
- Framework **enterprise-grade**: DI, guards, interceptors, i18n
- Standalone components (v21) → bundles optimizados
- Material Design → UI consistente sin diseñar desde cero
- Tipado TypeScript → refactor seguro en proyectos grandes

### ¿Por qué DuckDB?
- **OLAP embebido**: columnar, vectorizado, sin servidor
- Un archivo portable → demo en cualquier laptop
- SQL ANSI → migración futura a Snowflake trivial
- Performance analítica superior a SQLite para agregaciones

### ¿Por qué arquitectura Medallion?
- **Trazabilidad**: raw inmutable, reprocesamiento seguro
- **Calidad**: silver limpia antes de modelar
- **Gobernanza**: ctl_* audita cada carga
- Estándar industria (Databricks, Snowflake)

### ¿Por qué tablas AGG?
- Dashboard no puede hacer `GROUP BY` sobre 220k facts en cada request
- Materialización offline → lectura O(1) por KPI
- Mismo patrón que MVs en Snowflake o BigQuery scheduled queries

### ¿Por qué Repository Pattern?
- **Separa SQL de lógica de negocio**
- Testeable: mock repository sin DuckDB
- Un punto de cambio si migramos a Snowflake
- DRY: queries en `app/sql/*.sql`

### ¿Por qué Services?
- Routes delgadas (solo HTTP concerns)
- Cache, validación, composición de repos en un lugar
- Reutilizable entre `/api/v1` enterprise y `/api/v2`

### ¿Por qué Dashboard separado?
- **features/dashboard** = analytics hub (ECharts, KPIs warehouse)
- **packages/home** = experiencia streaming (Discover)
- Separación de concerns UX: consumidor vs analista

### ¿Por qué Recommendation Engine heurístico?
- **Explicable**: cada score tiene `reason` textual
- Sin GPU ni dataset de entrenamiento
- Determinístico → tests reproducibles
- Base para hybrid ML en v3.0

---

## 4. Demo sugerida (10 minutos)

1. **Login** demo/demo123
2. **Discover** — reproducir track, favorito
3. **Dashboard** `/dashboard` — KPIs, gráficos ECharts
4. **Recomendaciones** — explicar score y reason
5. **Explorer** (admin) — mostrar tablas warehouse
6. **Swagger** `/docs` — envelope API
7. **Health** `/health` — warehouse status

---

## 5. Preguntas difíciles del profesor

### ¿Por qué DuckDB y no PostgreSQL?

| Criterio | DuckDB | PostgreSQL |
|----------|--------|------------|
| Setup | Zero-config, archivo | Servidor + tuning |
| OLAP agregaciones | Optimizado columnar | Row-store, necesita índices |
| Portabilidad demo | Copiar un .duckdb | Dump/restore |
| Concurrencia writes | Limitada | Excelente |
| **Este proyecto** | Analytics local ~100k | Overkill para demo |

**Respuesta:** DuckDB es ideal para el scope académico. PostgreSQL sería la elección si tuviéramos miles de writes concurrentes (OLTP). La arquitectura Repository permite migrar sin reescribir servicios.

### ¿Por qué usar capas (Medallion)?

Sin capas, un error en limpieza corrompe el warehouse. Con capas:
- Bronze preserva evidencia original
- Silver es idempotente y re-ejecutable
- Gold es contract estable para la API

### ¿Cómo escala el sistema?

**Hoy:** vertical, single node, cache in-process.  
**Escala horizontal:**
1. Redis cache compartido
2. API stateless detrás load balancer
3. Warehouse → Snowflake (ELT con dbt)
4. CDN para SPA
5. Event streaming (Kafka) para facts en tiempo real

### ¿Cómo agregar IA?

1. Generar embeddings de tracks (audio features + metadata)
2. Almacenar en vector index
3. Scoring híbrido: `final = 0.6 * heuristic + 0.4 * cosine_similarity`
4. A/B test con métricas CTR
5. MLflow para versionado de modelos

### ¿Cómo migrar a Snowflake?

```sql
-- Export desde DuckDB
COPY agg_daily_streams TO 'agg_daily_streams.parquet';
-- Snowflake
CREATE TABLE agg_daily_streams AS SELECT * FROM @stage/agg_daily_streams.parquet;
```
Cambiar `DuckDBClient` por connector Snowflake en repositories. Services y API sin cambios.

### ¿Cómo migrar a BigQuery?

Export Parquet → GCS → `bq load` → dbt models. Misma abstracción Repository.

### ¿Cómo soportar millones de usuarios?

| Componente | Solución |
|------------|----------|
| Auth | JWT + Redis sessions |
| API | K8s HPA, 10+ pods |
| Warehouse | Snowflake/BigQuery |
| Cache | Redis Cluster |
| ETL | Airflow + dbt incremental |
| Frontend | CDN CloudFront |

**Honestidad académica:** el proyecto actual demuestra **patrones** enterprise, no escala de millones out-of-the-box.

### ¿Por qué tres APIs (/v1 enterprise, /v1 legacy, /v2)?

Evolución incremental sin breaking changes. Enterprise es la superficie analítica estable; legacy mantiene streaming/auth; v2 es scaffold modular futuro.

### ¿Qué pasa si falla el ETL?

`/health` retorna `degraded`. API sirve catálogo desde dims existentes; dashboard muestra empty state. `ctl_pipeline_stages` registra la falla.

### ¿Es seguro para producción?

Baseline: bcrypt, rate limit, CORS, headers, no stack traces. Falta: WAF, secrets manager, pentest. Ver [security.md](../10-security/security.md).

---

## 6. Métricas para mencionar

| Métrica | Valor |
|---------|------:|
| Endpoints API | 93 |
| Tablas warehouse | 48 |
| Líneas backend Python | ~12,000 |
| Líneas frontend | ~26,000 |
| Cobertura tests backend | ~75% |
| Componentes Angular | 46 |

---

## 7. Cierre recomendado

> VOXMETRIK_V2 demuestra competencias full-stack y data engineering: modelado dimensional, ETL Medallion, API production-ready y UX streaming. La arquitectura está preparada para evolucionar hacia Snowflake, ML híbrido y despliegue cloud sin reescribir el dominio de negocio.

---

## Referencias rápidas

- [architecture.md](../02-architecture/architecture.md)
- [database.md](../03-database/database.md)
- [audit-report.md](../12-audit/audit-report.md)
- [roadmap.md](../14-roadmap/roadmap.md)
