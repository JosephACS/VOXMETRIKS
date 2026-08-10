# VOXMETRIKS — Estado actual del producto

**Única verdad vigente de capacidades.**  
**Referencia Git:** `main @ 49ecc7a2` y cambios posteriores aceptados por CI.
**Specs históricas:** [`.specify/history/`](../.specify/history/README.md) — no sustituyen este documento.

## Capacidades implementadas

| Área | Evidencia en repo |
|------|-------------------|
| Identidad / sesiones / preferencias | `apps/backend` identity; login SPA |
| Organizaciones + membresías + RBAC | packages organizations |
| Suscripciones org + planes | subscriptions |
| Billing (invoices, payments, refunds, credit notes, manual transfer) | billing; idempotencia org-scoped |
| Suscripciones personales B2C + household profiles | personal_subscriptions; profile security |
| Catálogo / favoritos / playlists / búsqueda | streaming + catalog |
| Reproducción (resolver + player) | playback-core / music player |
| Unified Music Search (núcleo) | backend `/tracks/music-search`, adopt, repair-source; frontend local → YouTube → adopt; pruebas asociadas |
| Artist Space + invitaciones | artist_space (046) |
| Catalog rights / contracts | catalog_rights |
| Reportes simples / workpanel / complex | reports packages |
| Platform ops (parcial) | platform_ops |
| ELT DuckDB | `analytics/elt` (`elt_pipeline.py` canónico) |
| Orquestación ELT Airflow (Spec 048) | DAG de ocho tareas + LocalExecutor; smoke Docker/Airflow verificado en CI |
| Compose canónico app | `compose.yml` (`backend`, `frontend`) |

## Capacidades parciales

| Área | Limitación real |
|------|-----------------|
| CRM comercial | Flujos UI/API presentes; lifecycle/conversion con deuda |
| Campaigns / ROI | Módulo presente; métricas no certificadas |
| Business analytics / engagement | Parcial; sin inventar KPIs |
| Compliance / CS / support | Esqueleto o parcial |
| Smart recommendations / AI helpers | Reglas locales; no LLM obligatorio |
| Royalties | Simulado / diferido — no payouts reales |
| Unified Music Search (alcance avanzado) | Núcleo implementado; pendiente smoke con API key/proveedor real y alcance avanzado no aprobado |

## Decisiones diferidas (sin inventar parámetros)

- Pasarela de pago real y precios/umbrales finales de trial/cancel.
- Streaming comercial licenciado.
- Monetización/royalties reales.
- Alcance avanzado de music search / escrituras de catálogo no aprobadas.
- Numeración histórica **030** (colisión royalties vs paquetes posteriores).

## Limitaciones reales

- Entorno académico / demo; DuckDB no es OLTP de producción.
- Airflow es una capacidad académica/demo verificada en Docker CI; no se afirma HA ni producción.
- Audio vía contrato YouTube Data API / proveedores aprobados + demos.
- Docker opcional según host para la app; **Docker es requerido** para ejecutar el stack Airflow.
- Sin métricas inventadas de cobertura, concurrencia o ROI.
- DuckDB single-writer: no ejecutar aplicación y DAG Airflow contra el mismo warehouse a la vez.

## Gates actuales

| Gate | Comando |
|------|---------|
| API smoke | `python -c "from app.main import create_app; create_app()"` (cwd `apps/backend`) |
| Backend | `python -m pytest -q` |
| Frontend | `npm run lint` · `npm test` · `npm run build` |
| Docker | `docker compose up --build` (tras `make pipeline` en instalación nueva) |
| Spec Kit paths | `.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json` |

## Módulos de código (mapa breve)

`identity`, `organizations`, `subscriptions`, `billing`, `personal_subscriptions`, `crm`, `catalog` / streaming, `artist_space`, `catalog_rights`, `campaigns`, `royalties` (simulado), `reports`, `platform_ops`, `compliance`, playback-core / music-search.
