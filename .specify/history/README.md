# Índice histórico de Specs (001–047)

Fuente Spec Kit: [`.specify/README.md`](../README.md).
Estado actual del producto: [`docs/STATUS.md`](../../docs/STATUS.md).
Mapa de capacidades: [`../CAPABILITY_MAP.md`](../CAPABILITY_MAP.md).

## Leyenda

| Etiqueta | Significado |
|----------|-------------|
| histórico | Spec/documentación de diseño o entrega pasada (spec.md original preservado) |
| HISTORICAL_RECONSTRUCTED | Spec reconstruida; original no disponible en Git |
| implementado / parcial / diferido / cerrado | Alineado a vocabulario de `docs/STATUS.md` / closures — **STATUS manda** |
| colisión 030 | Numeración histórica documentada; **no** inventar otro ID |

## Inventario físico

Exactamente **48** carpetas (`001`–`048`), cada una con `spec.md`.
`closure.md` presente cuando hay evidencia real o reconstrucción verificable (022–023 y 032–048).

## 001–021 · 024–031 (originales preservados)

| ID | Carpeta | Notas |
|----|---------|-------|
| 001 | [001-user-identity-access](001-user-identity-access/spec.md) | histórico / implementado |
| 002 | [002-personal-music-library](002-personal-music-library/spec.md) | histórico / implementado |
| 003 | [003-catalog-discovery](003-catalog-discovery/spec.md) | histórico / implementado |
| 004 | [004-listening-experience](004-listening-experience/spec.md) | histórico / implementado |
| 005 | [005-personalized-discovery](005-personalized-discovery/spec.md) | histórico / parcial |
| 006 | [006-account-self-service](006-account-self-service/spec.md) | histórico / implementado |
| 007 | [007-operational-analytics-dashboards](007-operational-analytics-dashboards/spec.md) | histórico / implementado |
| 008 | [008-pipeline-monitoring](008-pipeline-monitoring/spec.md) | histórico / implementado |
| 009 | [009-data-explorer](009-data-explorer/spec.md) | histórico / implementado |
| 010 | [010-catalog-steward](010-catalog-steward/spec.md) | histórico / implementado |
| 011 | [011-health-operations](011-health-operations/spec.md) | histórico / implementado |
| 012 | [012-auto-quality-gates](012-auto-quality-gates/spec.md) | histórico / implementado |
| 013 | [013-academic-defense-deliverables](013-academic-defense-deliverables/spec.md) | histórico / cerrado |
| 014 | [014-repository-stabilization-domain-foundation](014-repository-stabilization-domain-foundation/spec.md) | histórico / implementado |
| 015 | [015-enterprise-business-foundation](015-enterprise-business-foundation/spec.md) | histórico / reemplazado por docs de producto |
| 016 | [016-identity-and-organizations](016-identity-and-organizations/spec.md) | histórico / implementado |
| 017 | [017-crm-and-commercial-contracting](017-crm-and-commercial-contracting/spec.md) | histórico / parcial |
| 018 | [018-plans-and-subscriptions](018-plans-and-subscriptions/spec.md) | histórico / implementado |
| 019 | [019-billing-payments-and-reconciliation](019-billing-payments-and-reconciliation/spec.md) | histórico / implementado |
| 020 | [020-artists-and-team-management](020-artists-and-team-management/spec.md) | histórico / parcial → evoluciona 046 |
| 021 | [021-catalog-rights-and-contracts](021-catalog-rights-and-contracts/spec.md) | histórico / implementado |
| 024 | [024-executive-reporting-and-business-decisions](024-executive-reporting-and-business-decisions/spec.md) | histórico / implementado |
| 025 | [025-customer-success-and-support](025-customer-success-and-support/spec.md) | histórico / parcial |
| 026 | [026-compliance-privacy-and-global-audit](026-compliance-privacy-and-global-audit/spec.md) | histórico / parcial |
| 027 | [027-platform-operations-and-integrations](027-platform-operations-and-integrations/spec.md) | histórico / parcial |
| 028 | [028-enterprise-integration-and-final-validation](028-enterprise-integration-and-final-validation/spec.md) | histórico / cerrado |
| 029 | [029-personal-music-subscriptions](029-personal-music-subscriptions/spec.md) | histórico / implementado |
| 030 | [030-royalties-settlements-and-simulated-payouts](030-royalties-settlements-and-simulated-payouts/spec.md) | histórico / diferido — **colisión histórica del número 030**; sin monetización real |
| 031 | [031-artist-music-submission-catalog-review-and-release-publishing](031-artist-music-submission-catalog-review-and-release-publishing/spec.md) | histórico / parcial |

## 022–023 (reconstruidas desde evidence Git)

| ID | Carpeta | Fuentes |
|----|---------|---------|
| 022 | [022-campaigns-budgets-and-roi](022-campaigns-budgets-and-roi/) | `d2f6a27f:automation/specs/022-…/evidence/*` |
| 023 | [023-engagement-and-business-analytics](023-engagement-and-business-analytics/) | `d2f6a27f:automation/specs/023-…/evidence/*` |

## 032–044 (reconstruidas; original no en Git)

Cada carpeta incluye `spec.md` + `closure.md` con `HISTORICAL_RECONSTRUCTED`.
Fuentes mínimas: este índice, Spec 047, `docs/STATUS.md`, código/pruebas, commits listados en cada closure.

| ID | Carpeta |
|----|---------|
| 032 | [032-product-integration-completion](032-product-integration-completion/) |
| 033 | [033-playable-music-youtube-official](033-playable-music-youtube-official/) |
| 034 | [034-role-based-navigation-simplification](034-role-based-navigation-simplification/) |
| 035 | [035-listener-activity](035-listener-activity/) |
| 036 | [036-enterprise-product-audit](036-enterprise-product-audit/) |
| 037 | [037-functional-security-org-isolation-catalog-cycle](037-functional-security-org-isolation-catalog-cycle/) |
| 038 | [038-controlled-product-simplification](038-controlled-product-simplification/) |
| 039 | [039-final-integral-validation-delivery](039-final-integral-validation-delivery/) |
| 040 | [040-essential-enterprise-consolidation](040-essential-enterprise-consolidation/) |
| 041 | [041-repository-structure-spec-cleanup](041-repository-structure-spec-cleanup/) |
| 042 | [042-reproducible-docker-runtime](042-reproducible-docker-runtime/) |
| 043 | [043-professional-ux-visual-redesign](043-professional-ux-visual-redesign/) |
| 044 | [044-product-consolidation-data-clarity](044-product-consolidation-data-clarity/) |

## 045–052 (cerradas; movidas desde features/)

| ID | Carpeta | Estado |
|----|---------|--------|
| 045 | [045-spaces-contextual-navigation](045-spaces-contextual-navigation/) | cerrado |
| 046 | [046-artist-identity-access](046-artist-identity-access/) | cerrado |
| 047 | [047-repository-recovery-hardening](047-repository-recovery-hardening/) | cerrado |
| 048 | [048-airflow-elt-orchestration](048-airflow-elt-orchestration/) | cerrado; smoke Docker/Airflow verificado |
| 049 | [049-taf14-strategic-agg-closure](049-taf14-strategic-agg-closure/) | cerrado; TAF14 Estratégico AGG OE-01…OE-08; smoke desktop/móvil |
| 050 | [050-identity-first-access](050-identity-first-access/) | cerrado; bootstrap de sesión, primer acceso e invitaciones durables |
| 051 | [051-artist-professional-journey](051-artist-professional-journey/) | cerrado; acceso, Artist Space, equipo, publicación y revisión independiente |
| 052 | [052-professional-checkout-journey](052-professional-checkout-journey/) | cerrado; checkout personal y empresarial con pago simulado profesional |

Cada una conserva `spec.md` + `closure.md` originales del cierre Spec Kit.

## Próxima Spec

La Spec **053** está activa bajo `.specify/features/053-organization-professional-journey/`. El siguiente ID disponible será **054** después de su cierre.
