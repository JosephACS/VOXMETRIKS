# Business Rules — Spec 030

1. **Platform income ≠ distributable pool.** Invoice/payment totals (B2C Spec 029 · B2B Spec 019) are platform income. A royalty pool amount is a separate approved balance. UI/API never equate `gross_income` with `distributable_amount`.

2. **B2C settled → pool candidates by default.** Settled personal payments may appear as contribution *candidates*. They enter the pool only after finance **approval** (`contribution_status=approved`). Draft/candidate amounts are not allocatable.

3. **B2B only via MANUAL_ATTRIBUTION.** Enterprise settled payments never auto-enter pools. Inclusion requires an explicit `MANUAL_ATTRIBUTION` record (actor, reason, amount, source payment/invoice ids) written to the append-only audit log.

4. **No universal artist %.** There is no platform-wide default royalty percentage for artists. Ownership comes exclusively from Spec 021 `app_rights_contract_party.ownership_percentage` for the scoped contract used in settlement.

5. **Streams ≠ money.** `fact_streaming` / aggregates supply **weights** for `PRO_RATA_STREAM_SHARE`. Streams create money only when an **approved pool** and a valid **attribution rule** are present.

6. **Attribution modes (closed set).**
   - `PRO_RATA_STREAM_SHARE` — split distributable amount by relative eligible streams in the pool period, then apply ownership %.
   - `MANUAL_ATTRIBUTION` — explicit audited shares/amounts; required path for B2B and optional for exception B2C.

7. **Ownership must sum 100%.** Settlement rejects contracts whose parties’ `ownership_percentage` do not sum to **100%** (tolerance 0 within Decimal quantize). Overlap/conflict from Spec 021 (`disputed`) also blocks settlement for that asset scope.

8. **Decimal money only.** All cash fields use `Decimal` / `DECIMAL(18,4)`. Float arithmetic for pool/settlement/payout is forbidden.

9. **Simulated payouts only.** Payout rows carry `simulated_*` statuses and MOCK provider labels. No PAN, IBAN, or live transfer execution.

10. **Taxes / withholding OUT_OF_SCOPE.** No tax calculation, retention, or fiscal remittance in this spec.

11. **Idempotent settlement/payout attempts.** Duplicate `idempotency_key` returns the existing settlement or simulated payout run.

12. **Audit on mutation.** Pool approve, contribution approve, MANUAL_ATTRIBUTION, settle, and simulate-payout write `app_royalty_event` (append-only).
