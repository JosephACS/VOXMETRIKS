# Capability map — VOXMETRIKS

Mapa de **11 familias** → Specs históricas relacionadas → packages actuales → estado enlazado a [`docs/STATUS.md`](../docs/STATUS.md).

**Regla:** este archivo **no** duplica la verdad de runtime. Si STATUS y este mapa discrepan, **gana STATUS**.

| # | Familia | Specs relacionadas (history) | Packages / áreas de código | Estado (STATUS) | Deudas / diferidos conocidos |
|---|---------|------------------------------|----------------------------|-----------------|------------------------------|
| 1 | Identidad y seguridad | 001, 006, 016, 037, 046, 050 | `identity`, `users`, `platform_rbac` | Implementado (sesión, bootstrap, primer acceso y preferencias); hardening parcial | Auth formal externa / IdP no afirmado |
| 2 | Organizaciones / RBAC | 016, 037, 045, 053, 054 | `organizations`, `platform_rbac`, navegación frontend | Recorrido profesional y paridad de superficies por permiso implementados | El backend continúa siendo autoridad de acceso |
| 3 | Experiencia musical del oyente | 002–005, 033, 035, 043, 044 | `streaming`, `apps/frontend/src/app/playback-core`, frontend home/search/player | Implementado (catálogo/favoritos/playlists/reproducción); music-search núcleo implementado | Smoke API key real; alcance avanzado music-search diferido |
| 4 | Suscripciones personales / household | 029, 037, 052 | `personal_subscriptions` | Suscripciones y checkout simulado profesional implementados | Pasarela real / precios finales diferidos |
| 5 | Artist Space | 020, 031, 045, 046, 051 | `apps/backend/app/packages/artists/identity_access`, `catalog_publishing`, `apps/frontend/src/app/packages/artist-space` | Implementado: acceso, perfil, equipo, música y publicación profesional | Pagos y monetización de artista diferidos |
| 6 | Catálogo / publicación / derechos | 003, 010, 021, 031, 051 | `catalog`, `catalog_rights`, `catalog_publishing`, `contracts` | Publishing artist-scoped y organización multi-artista implementados; Rights implementado | Flujos legales y liquidación avanzada diferidos |
| 7 | CRM / campañas / customer success | 017, 022, 025 | `crm`, `campaigns`, `customer_success` | Parcial | ROI no certificado; E2E campaigns; lifecycle CRM |
| 8 | Suscripciones / billing / royalties | 018, 019, 030, 040, 052 | `subscriptions`, `billing`, `royalties` | Billing/subs y checkout simulado profesional implementados; royalties **simulado/diferido** | Pasarela/payouts reales; **colisión histórica ID 030** |
| 9 | ELT / warehouse / calidad | 007–012, 014, 048 | `analytics`, ELT `analytics/elt`, `infrastructure/airflow`, explorer | Implementado (ELT DuckDB + orquestación Airflow demo verificada) | Single-writer; Airflow manual, sin HA |
| 10 | Operativo / táctico / estratégico | 007, 023, 024, 028, 040, **049** | `workpanel`, `reporting`, `simple_reports`, `complex_reports`, `business_analytics`, `engagement` | Reportes simples, Workpanel y reportes complejos: **implementados**. Spec **049** cerrada: Estratégico AGG (OE-01…OE-08 + `agg_strategic_kpi_period`) con smoke desktop/móvil. Business analytics: **parcial** (ROI no certificado; sin IA estratégica). | Metas comerciales diferidas; ROI no certificado |
| 11 | Platform Ops / compliance / runtime | 011, 026, 027, 039, 041, 042, 047; activa 055 | `platform_ops`, `compliance`, `compose.yml`, `scripts/start.ps1` | Ops funcional; recorrido profesional Platform Admin en consolidación; compliance parcial | Docker opcional en PATH; compliance parcial |

## Notas

- Specs **032–044** son `HISTORICAL_RECONSTRUCTED`; no afirman completitud por sí solas.
- Feature activa: **055 Platform Admin Professional Journey** — ver [`.specify/features/README.md`](features/README.md).
- Índice histórico: [`.specify/history/README.md`](history/README.md).
- Specs **050–054** están cerradas en history. **055** está activa; no crear otra Spec hasta su cierre.
