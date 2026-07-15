# Data model — Spec 030

## Tables (additive)

Idempotent `CREATE TABLE IF NOT EXISTS` via
`apps/backend/app/packages/royalties/infrastructure/schema.py`.

| Table | Purpose |
|-------|---------|
| `app_royalty_revenue_pool` | Period pool: `organization_id` nullable (platform B2C), currency, period, status (`draft`/`approved`/`processing`/`allocated`/`closed`/`canceled`), `attribution_method` (`PRO_RATA_STREAM_SHARE` \| `MANUAL_ATTRIBUTION`), `total_amount` / `residual_amount` Decimal, `is_demo`, unique `idempotency_key` |
| `app_royalty_revenue_source` | Pool contribution: `B2C_PERSONAL_PAYMENT` or `B2B_MANUAL` (audited), amount Decimal, status `candidate`/`approved`/`rejected` |
| `app_royalty_settlement_run` | Settlement run: pool_id, status lifecycle through `finalized`/`reversed`, Decimal totals, unique `idempotency_key`, optional `block_conflict_id` |
| `app_royalty_asset_allocation` | Per-asset stream share / attributable Decimal; `status` `ok`/`blocked` |
| `app_royalty_party_allocation` | Ownership × asset share → party Decimal lines |
| `app_royalty_adjustment` | Audited adjustment rows on a settlement (optional party line) |
| `app_royalty_statement` | Beneficiary statement: gross/adj/net Decimal; `draft`/`issued`/`paid_simulated` |
| `app_payout_batch` | Simulated payout batch (MOCK only) |
| `app_payout_instruction` | Per-statement simulated instruction; destination `demo_wallet` / `demo_bank_reference` / `simulated_account_token` (never real bank vault) |
| `app_payout_event` | Append-only simulated payout events |
| `app_payout_failure` | Simulated failure records |
| `app_royalty_audit_event` | Append-only royalty domain audit |
| `app_royalty_demo_stream_weight` | Synthetic track weights for tests without warehouse lock |

## Money

- Columns: `DECIMAL(18,4)` (align Spec 019 billing); participation `DECIMAL(18,8)`.
- Domain: `decimal.Decimal` only — no float arithmetic for cash.
- Rounding: quantize; remainder to largest share (ties by `asset_id`, then `party_id`).

## Relationships

- Source → optional personal payment / invoice ids (no cascade delete of billing).
- Settlement → Spec 021 `app_rights_contract` + `app_rights_contract_party` (ownership must sum **100%**).
- Stream weights → read-only `fact_streaming` aggregates for pool period, or demo/synthetic weights.
- Blocked ownership may insert into `app_rights_conflict` when that table exists.

## Hard rules

- Platform income ≠ distributable pool.
- B2C settled may feed pool candidates; B2B only via `MANUAL_ATTRIBUTION` audited.
- Streams never become money without approved pool + attribution rule.
- No universal artist %.
- Simulated payouts only — no real money / bank data.

## Unchanged

- Billing tables Spec 019/029
- Rights tables Spec 021 (read + validate 100%; no legal claims)
