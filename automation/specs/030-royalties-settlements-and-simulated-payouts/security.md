# Security — Spec 030

- Org-scoped reads/writes via `X-Organization-Id` where org pools apply; cross-org → `NotFoundError`
- Platform finance endpoints require `royalty.*` / `ops.*` as listed in API contracts
- MANUAL_ATTRIBUTION always records `actor_user_id`, reason, source ids — no silent B2B inject
- Contribution approve and settle are privilege-separated (`royalty.approve_pool` vs `royalty.settle`)
- Settlement/payout idempotency keys UNIQUE
- `app_royalty_event` append-only (no UPDATE/DELETE of audit rows)
- No bank account / IBAN / PAN storage
- Simulated payout responses labeled MOCK; never claim external transfer success
- Artists/org members with `royalty.view` see own statement lines only (IDOR blocked)
- Stream weight queries are read-only against warehouse — no mutation of `fact_streaming`
- Decimal parsing rejects non-finite / float-silent coercion paths in request bodies
