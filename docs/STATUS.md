# VOXMETRIKS — Estado actual del producto

**Única verdad vigente de capacidades.**  
**Referencia Git:** `main @ 4e987de7` y cambios posteriores aceptados por CI.
**Specs históricas:** [`.specify/history/`](../.specify/history/README.md) — no sustituyen este documento.

## Capacidades implementadas

| Área | Evidencia en repo |
|------|-------------------|
| Identidad / sesiones / preferencias | `apps/backend` identity; login SPA |
| Organizaciones + membresías + RBAC | packages organizations; recorrido profesional en consolidación (053) |
| Suscripciones org + planes | subscriptions; checkout profesional con pago simulado (052) |
| Billing (invoices, payments, refunds, credit notes, manual transfer) | billing; idempotencia org-scoped; orquestación checkout 052 |
| Suscripciones personales B2C + household profiles | personal_subscriptions; profile security; checkout profesional 052 |
| Catálogo / favoritos / playlists / búsqueda | streaming + catalog |
| Reproducción (resolver + player) | playback-core / music player |
| Unified Music Search (núcleo) | backend `/tracks/music-search`, adopt, repair-source; frontend local → YouTube → adopt; pruebas asociadas |
| Artist Space profesional + publicación independiente | artist_space, identity_access y catalog_publishing (051) |
| Catalog rights / contracts | catalog_rights |
| Reportes simples / workpanel / complex | reports packages |
| Business analytics / Estratégico AGG (049) | `agg_strategic_kpi_period`; overview OE-01…OE-08; dashboard Dirección estratégica; acceso CTA desde Reportes/Workpanel |
| Navegación contextual consolidada | Listener: Descubrir/Buscar/Biblioteca/Config; Admin: Workpanel/Catálogo/Org/Reportes/Plan; Engineer: ELT/Workpanel/Explorer/Reportes |
| Reproducción (resolver) | Catálogo = metadatos/portada; YouTube = fuente; matching con scoring; fallback silencioso |
| Platform ops (parcial) | platform_ops |
| ELT DuckDB | `analytics/elt` (`elt_pipeline.py` canónico) |
| Orquestación ELT Airflow (Spec 048) | DAG de ocho tareas + LocalExecutor; smoke Docker/Airflow verificado en CI |
| Compose canónico app | `compose.yml` (`backend`, `frontend`) |

## Capacidades parciales

| Área | Limitación real |
|------|-----------------|
| CRM comercial | Flujos UI/API presentes; lifecycle/conversion con deuda |
| Business analytics / engagement | Parcial: AGG estratégico OE visible; ROI no certificado; sin IA estratégica; metas comerciales diferidas |
| Campaigns / ROI | Módulo presente; métricas no certificadas |
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
