# Capability map — VOXMETRIKS

Mapa de **11 familias** → Specs históricas relacionadas → packages actuales → estado enlazado a [`docs/STATUS.md`](../docs/STATUS.md).

**Regla:** este archivo **no** duplica la verdad de runtime. Si STATUS y este mapa discrepan, **gana STATUS**.

| # | Familia | Specs relacionadas (history) | Packages / áreas de código | Estado (STATUS) | Deudas / diferidos conocidos |
|---|---------|------------------------------|----------------------------|-----------------|------------------------------|
| 1 | Identidad y seguridad | 001, 006, 016, 037, 046, 050 | `identity`, `users`, `platform_rbac` | Implementado (sesión, bootstrap, primer acceso y preferencias); hardening parcial | Auth formal externa / IdP no afirmado |
| 2 | Organizaciones / RBAC | 016, 037, 045 | `organizations`, `platform_rbac` | Implementado | Matriz de capabilities avanzada según deuda de módulos parciales |
| 3 | Experiencia musical del oyente | 002–005, 033, 035, 043, 044 | `streaming`, `apps/frontend/src/app/playback-core`, frontend home/search/player | Implementado (catálogo/favoritos/playlists/reproducción); music-search núcleo implementado | Smoke API key real; alcance avanzado music-search diferido |
| 4 | Suscripciones personales / household | 029, 037 | `personal_subscriptions` | Implementado | Pasarela real / precios finales diferidos |
| 5 | Artist Space | 020, 031, 045, 046; activa 051 | `apps/backend/app/packages/artists/identity_access`, `catalog_publishing`, `apps/frontend/src/app/packages/artist-space` | Space e invitaciones implementados; consolidación profesional 051 diseñada/activa | Pagos y monetización de artista fuera de 051 |
| 6 | Catálogo / publicación / derechos | 003, 010, 021, 031 | `catalog`, `catalog_rights`, `catalog_publishing`, `contracts` | Rights implementado; publishing parcial | Ciclo completo de release según deuda 031 |
| 7 | CRM / campañas / customer success | 017, 022, 025 | `crm`, `campaigns`, `customer_success` | Parcial | ROI no certificado; E2E campaigns; lifecycle CRM |
| 8 | Suscripciones / billing / royalties | 018, 019, 030, 040 | `subscriptions`, `billing`, `royalties` | Billing/subs implementados; royalties **simulado/diferido** | Payouts reales; pasarela; **colisión histórica ID 030** |
| 9 | ELT / warehouse / calidad | 007–012, 014, 048 | `analytics`, ELT `analytics/elt`, `infrastructure/airflow`, explorer | Implementado (ELT DuckDB + orquestación Airflow demo verificada) | Single-writer; Airflow manual, sin HA |
| 10 | Operativo / táctico / estratégico | 007, 023, 024, 028, 040, **049** | `workpanel`, `reporting`, `simple_reports`, `complex_reports`, `business_analytics`, `engagement` | Reportes simples, Workpanel y reportes complejos: **implementados**. Spec **049** cerrada: Estratégico AGG (OE-01…OE-08 + `agg_strategic_kpi_period`) con smoke desktop/móvil. Business analytics: **parcial** (ROI no certificado; sin IA estratégica). | Metas comerciales diferidas; ROI no certificado |
| 11 | Platform Ops / compliance / runtime | 011, 026, 027, 039, 041, 042, 047 | `platform_ops`, `compliance`, `compose.yml`, `scripts/start_demo.ps1` | Ops/compliance parcial; Compose canónico; demo endurecida | Docker opcional en PATH; compliance esqueleto |

## Notas

- Specs **032–044** son `HISTORICAL_RECONSTRUCTED`; no afirman completitud por sí solas.
- Feature activa: **051 Professional Artist Journey** — ver [`.specify/features/README.md`](features/README.md).
- Índice histórico: [`.specify/history/README.md`](history/README.md).
- Spec **050** está cerrada en history. **051** está activa; el siguiente identificador disponible será **052**.
