# Capability map — VOXMETRIKS

Mapa de **11 familias** → Specs históricas relacionadas → packages actuales → estado enlazado a [`docs/STATUS.md`](../docs/STATUS.md).

**Regla:** este archivo **no** duplica la verdad de runtime. Si STATUS y este mapa discrepan, **gana STATUS**.

| # | Familia | Specs relacionadas (history) | Packages / áreas de código | Estado (STATUS) | Deudas / diferidos conocidos |
|---|---------|------------------------------|----------------------------|-----------------|------------------------------|
| 1 | Identidad y seguridad | 001, 006, 016, 037, 046 | `identity`, `users`, `platform_rbac` | Implementado (sesiones/preferencias); hardening parcial | Auth formal externa / IdP no afirmado |
| 2 | Organizaciones / RBAC | 016, 037, 045 | `organizations`, `platform_rbac` | Implementado | Matriz de capabilities avanzada según deuda de módulos parciales |
| 3 | Experiencia musical del oyente | 002–005, 033, 035, 043, 044 | `streaming`, `apps/frontend/src/app/playback-core`, frontend home/search/player | Implementado (catálogo/favoritos/playlists/reproducción); music-search núcleo implementado | Smoke API key real; alcance avanzado music-search diferido |
| 4 | Suscripciones personales / household | 029, 037 | `personal_subscriptions` | Implementado | Pasarela real / precios finales diferidos |
| 5 | Artist Space | 020, 031, 045, 046 | `apps/backend/app/packages/artists/identity_access`, `catalog_publishing`, `apps/frontend/src/app/packages/artist-space` | Implementado (space + invitaciones) | Planes de artista / monetización artista: futura Spec, únicamente si producto aprueba ese alcance |
| 6 | Catálogo / publicación / derechos | 003, 010, 021, 031 | `catalog`, `catalog_rights`, `catalog_publishing`, `contracts` | Rights implementado; publishing parcial | Ciclo completo de release según deuda 031 |
| 7 | CRM / campañas / customer success | 017, 022, 025 | `crm`, `campaigns`, `customer_success` | Parcial | ROI no certificado; E2E campaigns; lifecycle CRM |
| 8 | Suscripciones / billing / royalties | 018, 019, 030, 040 | `subscriptions`, `billing`, `royalties` | Billing/subs implementados; royalties **simulado/diferido** | Payouts reales; pasarela; **colisión histórica ID 030** |
| 9 | ELT / warehouse / calidad | 007–012, 014 | `analytics`, ELT `analytics/elt`, explorer | Implementado (ELT DuckDB) | Agregados faltantes degradan gracefully |
| 10 | Operativo / táctico / estratégico | 007, 023, 024, 028, 040 | `workpanel`, `reporting`, `simple_reports`, `complex_reports`, `business_analytics`, `engagement` | Reportes simples, Workpanel y reportes complejos: **implementados** según `docs/STATUS.md`. Business analytics/engagement: **parcial**. Estratégico AGG: **pendiente de definición y aceptación**; candidato para la próxima Spec después de decisión de producto. No se afirma cierre completo Operativo/Táctico/Estratégico AGG. | Trends stubs; no inventar KPIs; AGG estratégico sin aceptación |
| 11 | Platform Ops / compliance / runtime | 011, 026, 027, 039, 041, 042, 047 | `platform_ops`, `compliance`, `compose.yml`, `scripts/start_demo.ps1` | Ops/compliance parcial; Compose canónico; demo endurecida | Docker opcional en PATH; compliance esqueleto |

## Notas

- Specs **032–044** son `HISTORICAL_RECONSTRUCTED`; no afirman completitud por sí solas.
- Features activas: ninguna — ver [`.specify/features/README.md`](features/README.md).
- Índice histórico: [`.specify/history/README.md`](history/README.md).
- El identificador **048** está reservado solo como siguiente número Spec Kit disponible; **no** se asigna aquí a un alcance de producto concreto.
