# Roadmap — Hoja de ruta

## Visión

Evolución de VOXMETRIK_V2 desde plataforma académica analítica hacia producto SaaS multi-tenant con capacidades ML y despliegue cloud-native.

---

## v2.1 — Estabilización (Q3 2026)

### Objetivos
Consolidar infraestructura production-ready y eliminar deuda técnica dual-stack.

### Mejoras
- Cache Redis distribuido
- Unificar `core/database.py` y `duckdb_client.py`
- Montar health routes enterprise (✅ hecho)
- CI/CD GitHub Actions con quality gates
- Screenshots reales en documentación

### Tecnologías
Redis, GitHub Actions, pre-commit hooks

### Impacto
Multi-worker Uvicorn seguro; deploy automatizado; -30% complejidad DB layer

---

## v2.5 — Observabilidad (Q4 2026)

### Objetivos
Visibilidad operacional nivel producción.

### Mejoras
- OpenTelemetry traces (FastAPI + DuckDB)
- Prometheus metrics (`/metrics`)
- Dashboard Grafana
- Alertas en logs (error rate, ETL failures)
- Sentry error tracking

### Tecnologías
OTel, Prometheus, Grafana, Sentry

### Impacto
MTTR < 15 min; detección proactiva de degradación warehouse

---

## v3.0 — Intelligence Layer (Q1 2027)

### Objetivos
Recomendaciones híbridas: heurístico + embeddings.

### Mejoras
- Vector store para track embeddings (pgvector o DuckDB VSS)
- Collaborative filtering matrix factorization
- A/B testing framework recomendaciones
- Personalización real-time en sesión
- Feature store para ML features

### Tecnologías
sentence-transformers, MLflow, Feast

### Impacto
+20% CTR recomendaciones; base para IA explicable

---

## Enterprise — Multi-tenant B2B (Q2 2027)

### Objetivos
Licenciamiento a labels, promotores y analistas musicales.

### Mejoras
- Tenancy por organización
- RBAC granular (admin, analyst, viewer)
- SSO SAML/OIDC
- Export PDF/Excel reportes
- API keys con quotas
- White-label frontend

### Tecnologías
Keycloak, Stripe Billing, Apache Superset embed

### Impacto
Modelo SaaS B2B; ingresos recurrentes

---

## Cloud — Escalabilidad global (Q3 2027)

### Objetivos
Migrar warehouse a cloud OLAP; frontend CDN global.

### Mejoras
- Snowflake / BigQuery como warehouse primario
- DuckDB como cache edge local
- Kubernetes (EKS/GKE) para API
- CDN CloudFront para SPA
- Event-driven ETL (Kafka → dbt)
- Disaster recovery multi-region

### Tecnologías
Snowflake, dbt, Terraform, Kubernetes, Kafka

### Impacto
Escala a millones de eventos/día; SLA 99.9%

---

## Matriz de priorización

| Versión | Esfuerzo | Valor negocio | Riesgo técnico |
|---------|----------|---------------|----------------|
| v2.1 | Bajo | Medio | Bajo |
| v2.5 | Medio | Alto | Bajo |
| v3.0 | Alto | Muy alto | Medio |
| Enterprise | Alto | Muy alto | Medio |
| Cloud | Muy alto | Estratégico | Alto |

Ver [audit-report.md](../12-audit/audit-report.md) para estado actual.
