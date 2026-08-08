> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 030 — Royalties, Settlements and Simulated Payouts

**Status:** CLOSED_WITH_ACCEPTED_DEBT
**Date:** 2026-07-14
**Preceding:** Spec 021 (Catalog Rights) · Spec 019/029 billing money · Spec 028 enterprise closure
**Owner:** platform finance + org rights operators (never silent % on artists)

## Summary

VOXMETRIKS models **distributable royalty pools**, **settlements**, and **simulated payouts only**.
Platform income (B2C/B2B invoice totals) is **not** the distributable pool. Streams never become money without an **approved pool** + an **attribution rule**.

| Source | How it enters a pool |
|--------|----------------------|
| B2C settled payments (Spec 029) | Default candidate → finance **approve** into pool |
| B2B settled payments (Spec 019) | **Only** `MANUAL_ATTRIBUTION` explícita y auditada |
| Stream counts | Usage weights for `PRO_RATA_STREAM_SHARE` — never cash by themselves |

## User scenarios

1. Finance creates draft royalty pool (period + currency) → reviews B2C settled candidates → approves contributions
2. Rights operator attaches active Spec 021 contract (parties sum **100%** ownership) + chooses attribution rule
3. Run settlement → statement lines = pool amount × stream share × ownership % (Decimal)
4. B2B revenue excluded until explicit audited MANUAL_ATTRIBUTION
5. Simulate payout run → statuses `simulated_*` only · no bank rail
6. Artist/org views statement · cannot invent universal artist %

## Functional requirements

- FR1 Separar **platform income** vs **distributable pool** (ledger/UI labels)
- FR2 B2C settled → pool candidates; finance approval required before contribution
- FR3 B2B → sólo `MANUAL_ATTRIBUTION` con actor + motivo + audit append-only
- FR4 Attribution modes: `PRO_RATA_STREAM_SHARE` | `MANUAL_ATTRIBUTION`
- FR5 Rights contract parties must sum to **100%** `ownership_percentage` for settlement eligibility
- FR6 Decimal money (`DECIMAL(18,4)` / `Decimal`) — no float cash math
- FR7 Simulated payouts only (`simulated_pending` → `simulated_completed` / `simulated_failed`)
- FR8 REST `/api/v1/royalties/*` + FE package `royalties`
- FR9 Demo seed opt-in · taxes/withholding **OUT_OF_SCOPE**

## Assumptions

- Spec 021 rights contracts are the ownership source of truth
- Warehouse `fact_streaming` / aggregates supply stream weights (read-only)
- No real ACH/SWIFT/Stripe Connect payouts

## Success criteria

- Income totals ≠ pool totals in API/UI
- Settlement blocked without approved pool + rule + 100% ownership
- B2B contribution without MANUAL_ATTRIBUTION rejected
- Simulated payout never writes real external payment ids
- pytest S030 + existing enterprise/B2C gates remain green
