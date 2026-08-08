> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 024 — Executive Reporting and Business Decisions

**Status:** CLOSED_WITH_ACCEPTED_DEBT  
**Date:** 2026-07-12

Implements CAP-16 from Spec 015: executive report definitions, immutable snapshots, approval/publication, CSV export (academic, not certified), and business decisions with actions/follow-ups.

## Canonical APIs
- `/api/v1/reports`
- `/api/v1/business-decisions`

## Package
`apps/backend/app/packages/reporting/`

## Out of scope
- Royalties / payouts (future, unnumbered)
- Legal e-sign / certified financial statements
- Predictive AI reporting
