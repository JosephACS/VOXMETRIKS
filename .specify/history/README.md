# Índice histórico de Specs (001–047)

Fuente Spec Kit vigente: [`.specify/`](../).  
Estado actual del producto: [`docs/STATUS.md`](../../docs/STATUS.md).  
Snapshot documental previo: commit Git `d2f6a27f`.

## Leyenda

| Etiqueta | Significado |
|----------|-------------|
| histórico | Spec/documentación de diseño o entrega pasada |
| implementado | Capacidad presente en `main` con evidencia de código/pruebas |
| reemplazado | Superado por una consolidación o feature posterior |
| recuperado selectivamente | Paquetes 032–044 reintegrados vía 047 / commits posteriores |
| cerrado | Feature Spec Kit cerrada (045–047) |
| diferido | Decisión explícitamente aplazada |

## 001–031 (automation/specs → history)

| ID | Carpeta | Estado | Notas |
|----|---------|--------|-------|
| 001 | [001-user-identity-access](001-user-identity-access/spec.md) | histórico / implementado | Identidad y acceso |
| 002 | [002-personal-music-library](002-personal-music-library/spec.md) | histórico / implementado | Biblioteca personal |
| 003 | [003-catalog-discovery](003-catalog-discovery/spec.md) | histórico / implementado | Catálogo |
| 004 | [004-listening-experience](004-listening-experience/spec.md) | histórico / implementado | Escucha |
| 005 | [005-personalized-discovery](005-personalized-discovery/spec.md) | histórico / parcial | Descubrimiento / smart |
| 006 | [006-account-self-service](006-account-self-service/spec.md) | histórico / implementado | Cuenta |
| 007 | [007-operational-analytics-dashboards](007-operational-analytics-dashboards/spec.md) | histórico / implementado | Analytics |
| 008 | [008-pipeline-monitoring](008-pipeline-monitoring/spec.md) | histórico / implementado | Pipeline |
| 009 | [009-data-explorer](009-data-explorer/spec.md) | histórico / implementado | Explorer |
| 010 | [010-catalog-steward](010-catalog-steward/spec.md) | histórico / implementado | Steward |
| 011 | [011-health-operations](011-health-operations/spec.md) | histórico / implementado | Health / settings |
| 012 | [012-auto-quality-gates](012-auto-quality-gates/spec.md) | histórico / implementado | Quality gates |
| 013 | [013-academic-defense-deliverables](013-academic-defense-deliverables/spec.md) | histórico / cerrado | Defensa académica |
| 014 | [014-repository-stabilization-domain-foundation](014-repository-stabilization-domain-foundation/spec.md) | histórico / implementado | Monorepo / domains |
| 015 | [015-enterprise-business-foundation](015-enterprise-business-foundation/spec.md) | histórico / reemplazado | Modelo B2B → `docs/product/` |
| 016 | [016-identity-and-organizations](016-identity-and-organizations/spec.md) | histórico / implementado | Orgs |
| 017 | [017-crm-and-commercial-contracting](017-crm-and-commercial-contracting/spec.md) | histórico / parcial | CRM |
| 018 | [018-plans-and-subscriptions](018-plans-and-subscriptions/spec.md) | histórico / implementado | Suscripciones org |
| 019 | [019-billing-payments-and-reconciliation](019-billing-payments-and-reconciliation/spec.md) | histórico / implementado | Billing |
| 020 | [020-artists-and-team-management](020-artists-and-team-management/spec.md) | histórico / parcial | Artists (evoluciona 046) |
| 021 | [021-catalog-rights-and-contracts](021-catalog-rights-and-contracts/spec.md) | histórico / implementado | Rights |
| 022 | Campaigns, Budgets and ROI | histórico / parcial | Sin `spec.md` físico; solo evidence de cierre |
| 023 | Engagement and Business Analytics | histórico / parcial | Sin `spec.md` físico; solo evidence de cierre |
| 024 | [024-executive-reporting-and-business-decisions](024-executive-reporting-and-business-decisions/spec.md) | histórico / implementado | Reports |
| 025 | [025-customer-success-and-support](025-customer-success-and-support/spec.md) | histórico / parcial | CS / support |
| 026 | [026-compliance-privacy-and-global-audit](026-compliance-privacy-and-global-audit/spec.md) | histórico / parcial | Compliance |
| 027 | [027-platform-operations-and-integrations](027-platform-operations-and-integrations/spec.md) | histórico / parcial | Platform ops |
| 028 | [028-enterprise-integration-and-final-validation](028-enterprise-integration-and-final-validation/spec.md) | histórico / cerrado | Cierre enterprise |
| 029 | [029-personal-music-subscriptions](029-personal-music-subscriptions/spec.md) | histórico / implementado | Planes B2C |
| 030 | [030-royalties-settlements-and-simulated-payouts](030-royalties-settlements-and-simulated-payouts/spec.md) | histórico / diferido | **Colisión histórica del número 030** (royalties simulados vs numeración de paquetes posteriores); no monetización real |
| 031 | [031-artist-music-submission-catalog-review-and-release-publishing](031-artist-music-submission-catalog-review-and-release-publishing/spec.md) | histórico / parcial | Publishing |

## 032–044 (sin carpetas físicas en este repo)

**Fuente histórica de las Specs completas:** checkout antiguo **solo lectura**  
`C:\Users\Admin\Documents\Tarea\Proyectos\Ariosto\voxmetriks\automation\specs\032…044`  
(rama `feature/045-spaces-contextual-navigation` @ `e348d2cacf404fead63cc389c5d629a313b63626`).

**Hechos honestos:**
- Las Specs completas **no** existen en Git en `d2f6a27f` ni en este working tree.
- Están **excluidas físicamente** de la consolidación (no se copiaron aquí).
- El **resultado aprobado** de producto se recuperó **selectivamente** vía Spec **047** y paquetes/commits posteriores (music-core, enterprise residual, UX/infra) — ver [`docs/STATUS.md`](../../docs/STATUS.md).
- Al limpiar finalmente el checkout antiguo, las Specs completas **se perderán deliberadamente**, salvo decisión contraria de conservarlas fuera de este repo.

| ID | Título (checkout antiguo) | Disposición |
|----|---------------------------|-------------|
| 032 | Completar VOXMETRIKS como producto integrado | Excluida físicamente; resultado selectivo vía 047+ |
| 033 | Cierre del producto musical (playable + YouTube oficial) | Excluida físicamente; núcleo musical reconciliado después |
| 034 | Simplificación de navegación por roles | Excluida físicamente; resultado selectivo vía 047+ |
| 035 | Tu actividad (listener personal) | Excluida físicamente; resultado selectivo vía 047+ |
| 036 | Auditoría del producto empresarial (Fase 036) | Excluida físicamente; resultado selectivo vía 047+ |
| 037 | Seguridad funcional, aislamiento org y ciclo de catálogo | Excluida físicamente; resultado selectivo vía 047+ |
| 038 | Simplificación controlada del producto | Excluida físicamente; resultado selectivo vía 047+ |
| 039 | Validación integral final y entrega | Excluida físicamente; resultado selectivo vía 047+ |
| 040 | Consolidación empresarial esencial | Excluida físicamente; resultado selectivo vía 047+ |
| 041 | Estructura del repositorio y limpieza de specs | Excluida físicamente; resultado selectivo vía 047+ |
| 042 | Docker reproducible runtime | Excluida físicamente; Compose canónico retenido en raíz |
| 043 | Professional UX / visual redesign | Excluida físicamente; UX reconciliada después |
| 044 | Product consolidation and data clarity | Excluida físicamente; resultado selectivo vía 047+ |

## 045–047 (Spec Kit features vigentes como cierre)

| ID | Feature | Estado |
|----|---------|--------|
| 045 | [../features/045-spaces-contextual-navigation/](../features/045-spaces-contextual-navigation/) | cerrado |
| 046 | [../features/046-artist-identity-access/](../features/046-artist-identity-access/) | cerrado |
| 047 | [../features/047-repository-recovery-hardening/](../features/047-repository-recovery-hardening/) | cerrado |

Cada feature conserva solo `spec.md` + `closure.md`.
