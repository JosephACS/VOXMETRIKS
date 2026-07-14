# Security — Spec 029

- User scoped reads/writes via authenticated `user_id` (IDOR blocked on payment attempts/invoices/household)
- Invitation: SHA-256 hashed token, TTL 72h, single use
- Invite rate limit: 10/hour/owner
- Members cannot invite or manage billing
- Capacity Duo=2 Familiar=6 enforced server-side
- Payment idempotency key unique
- owner_type `user` vs organization isolation
- Audit via `personal_subscription_event`
- Tests force `EMAIL_PROVIDER=console`
- No PAN/CVV stored
- Platform admin cannot read private listening history via these APIs
