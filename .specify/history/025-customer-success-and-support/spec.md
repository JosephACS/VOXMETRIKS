> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 025 — Customer Success and Support

**Status:** CLOSED_WITH_ACCEPTED_DEBT  
**Date:** 2026-07-12

Implements CAP-17/CAP-18 from Spec 015: CS onboarding (distinct from org 016), rule-based health (not AI), risks/interventions, renewal/expansion, support cases with internal notes and academic SLA.

## Canonical APIs
- `/api/v1/customer-success`
- `/api/v1/support`

## Package
`apps/backend/app/packages/customer_success/`

## Out of scope
- Contractual SLA guarantees
- Royalties/payouts
- Predictive AI health
