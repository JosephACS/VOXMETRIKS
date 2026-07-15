# Accepted debt — Spec 030

1. Playwright E2E NOT_VERIFIED for `/royalties/*`
2. Simulated payouts only — no live bank / Stripe Connect / ACH
3. Taxes, withholding, and artist fiscal documents OUT_OF_SCOPE
4. Stream weight source uses existing aggregates; no new realtime stream→money pipeline
5. Auto-expiry of pool periods not implemented (manual archive)
6. Multi-currency FX conversion between pools OUT_OF_SCOPE (one currency per pool)
7. Rights legal certification still Spec 021 debt (tracking only)
8. Dedicated payout reconciliation cron deferred — simulate is on-demand API
