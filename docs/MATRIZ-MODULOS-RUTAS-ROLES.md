# Matriz módulos → rutas → roles

**Fecha:** 2026-07-15 · Fuente: dashboard-layout + routers + Specs 001–031
**Nota:** “Mi suscripción” personal = `/account/subscription`; empresarial = `/subscriptions/overview`.

| Área | Módulo | Qué hace | Ruta FE | API principal | Paquete BE | Tablas | Rol | Org | R/W | Demo | Estado | Deuda |
|------|--------|----------|---------|---------------|------------|--------|-----|-----|-----|------|--------|-------|
| Música | Inicio | Descubrir | `/discover` | catalog/stats | catalog/analytics | dim_* | usuario | no | R | listeners | OK | |
| Música | Playlists/Fav/Hist | Biblioteca | `/playlists` `/liked` `/history` | engagement | engagement | app playlist/fav | usuario | no | RW | listeners | OK | |
| B2C | Plan personal | Estado plan | `/account/subscription` | `/personal/*` | personal_subscriptions | personal_* | oyente | no | RW | free/premium | OK | mock pay |
| B2C | Planes | Catálogo Free–Familiar | `/account/plans` | `/personal/plans` | personal_subscriptions | — | oyente | no | R | free/premium | OK | |
| B2C | Factura personal | Cobros B2C | `/account/billing` | `/personal/invoices` | personal_subscriptions | personal_invoice | oyente | no | RW | premium | OK | |
| B2C | Household | Miembros Duo/Familiar | `/account/household` | `/personal/household` | personal_subscriptions | personal_household* | owner hogar | no | RW | household.owner | OK | |
| B2B | Org | Perfil miembros | `/organizations/:id/*` | `/organizations` | organizations | app_organization* | member+ | sí | RW | org.owner | OK | none→settings |
| B2B | Planes | Starter–Enterprise | `/subscriptions/plans` | `/plans` | subscriptions | app_plan* | billing+ | sí | R | org/finance | OK | legacy amounts retired |
| B2B | Suscripción org | Plan activo | `/subscriptions/overview` | `/subscriptions` | subscriptions | app_subscription* | billing+ | sí | RW | org.owner | OK | |
| B2B | Facturas | Cobros | `/billing/invoices` | `/billing/*` | billing | app_invoice* | finance | sí | RW | finance | OK | mock |
| CRM | Embudo | Leads/opps | `/crm/*` | `/crm/*` | crm | app_crm_* | sales_* | sí | RW | sales / demo.business | OK | |
| Derechos | Contratos | % ownership | `/catalog-rights/*` | `/catalog-rights` | catalog_rights | app_rights_* | rights/artist_mgr | sí | RW | artist/owner | OK | no legal cert |
| Artistas | Perfiles | Roster | `/artist-profiles` | `/artists` | artists | app_artist_* | artist_mgr | sí | RW | owner | OK | |
| Pub 031 | Portal | Lanzamientos | `/artist/*` | `/releases` `/artist-portal` | catalog_publishing | app_release_* | artist | sí | RW | demo.artist | OK | local media |
| Pub 031 | Review | Bandeja | `/catalog-review` | `/catalog-review` | catalog_publishing | app_release_review* | catalog_reviewer | sí | RW | admin/reviewer | OK | |
| Regalías 030 | Fondos/payouts | Distribución | `/royalties/*` `/payouts` | `/royalties` `/settlements` `/payouts` | royalties | app_royalty_* app_payout_* | finance | sí | RW* | finance; demo.business R | OK | simulado |
| Analytics | Musical | Charts | `/analytics` `/trending` | `/stats` `/analytics` | analytics | fact_* agg_* | user/eng | no | R | listeners | OK | sintético |
| Biz | Panel | KPI org | `/business-analytics` | `/business-analytics` | business_analytics | app_kpi* | org | sí | R | demo.business | OK | |
| Campañas | Marketing | Presupuestos | `/campaigns` | `/campaigns` | campaigns | app_campaign* | marketing | sí | RW | owner | OK | no causal IA |
| CS/Soporte | Casos | Tickets | `/customer-success` `/support` | CS routers | customer_success | app_* | CS | sí | RW | owner | OK | no IA predictiva |
| Compliance | Privacidad | Flujos académicos | `/compliance` | `/compliance` | compliance | app_* | compliance | sí | RW | admin | OK | no GDPR cert |
| Ops | Plataforma | Health/jobs | `/platform-ops` | `/platform-ops` | platform_ops | app_* | platform_admin | — | RW | platform.admin | OK | |
| Reportes | Ejecutivo | Decisiones | `/reports` `/business-decisions` | reporting | reporting | app_report* | org | sí | RW | owner | OK | |

\* demo.business: escritura peligrosa oculta en UI.

## Defectos revisados

| Hallazgo | Acción |
|----------|--------|
| Ambiguëdad “suscripción” B2C/B2B | Separar rutas `/account/*` vs `/subscriptions/*` (documentado) |
| Precios legacy 75/100/200/500 | Solo `_LEGACY_DEMO_AMOUNTS` | No catálogo activo |
| `organization_id=none` vs selector | Presentation muestra `/organizations/{id}/settings` cuando hay org activa | Verificar en demo |
| Media `data/media` ausente hasta upload | Esperado; seed/GP crean al usarse | WARN inventario |
