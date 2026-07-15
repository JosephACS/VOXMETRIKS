# Plan — Spec 030

## Approach

Additive DuckDB schema `app_royalty_*` + `app_simulated_payout*` under
`apps/backend/app/packages/royalties/`.
Reuse Spec 019/029 Decimal money helpers; reuse Spec 021 rights contracts for ownership.
Do **not** alter billing settlement semantics or invent a universal artist percentage.

## Workstreams

1. Schema + Decimal money entities + audit events
2. Pool lifecycle (draft → approved → settled) + B2C contribution candidates
3. Attribution rules (`PRO_RATA_STREAM_SHARE`, `MANUAL_ATTRIBUTION`)
4. Settlement engine + statement lines (ownership × stream share)
5. Simulated payout runs (no bank adapters)
6. HTTP `/api/v1/royalties` + platform/org RBAC
7. Frontend finance/royalties views + i18n labels income ≠ pool
8. Demo seed opt-in + tests + TRACEABILITY

## Out of scope

- Taxes / withholding / fiscal invoices for artists
- Real payout rails or bank account vaulting
- Universal default artist %
- Auto-feeding 100% of platform MRR into pools
- Changing Spec 021 conflict algorithms
