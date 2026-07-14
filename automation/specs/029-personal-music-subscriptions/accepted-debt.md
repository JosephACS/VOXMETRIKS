# Accepted debt — Spec 029

1. Playwright E2E NOT_VERIFIED for `/account/*`  
2. Advanced queue UX soft-gated (feature flag; no new queue redesign)  
3. Demo passwords only via env (`DEMO_PASSWORD`) — not seeded into git  
4. MOCK payments only  
5. Console email only under pytest  
6. Renewal cron is on-read (`finalize_period_end_cancellations` / grace) rather than dedicated job  
7. Platform admin price activate/deactivate via catalog upsert; no separate admin UI for personal prices  
