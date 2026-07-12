# Deferred Items — Spec 028

Items explicitly **not built** in this workspace closure.

## Specs not present

| Spec | Domain | Reason |
|------|--------|--------|
| 024 | Royalties accrual & statements | Spec file absent |
| 025 | Payout runs & banking | Spec file absent |
| 029 | (any follow-on) | Out of 028 scope per charter |

## Designed in 015, deferred implementation

| Capability | Planned API | Current state |
|------------|-------------|---------------|
| Customer Success | `/api/v1/customer-success` | **404** — no package |
| Support / ticketing | `/api/v1/support` | **404** — no package |
| Executive reports | `/api/v1/reporting/reports` | **404** — no package |

Validated by `test_enterprise_golden_path_s028.py::TestDeferredDomainsS028`.

## Golden-path steps deferred (implemented elsewhere, not chained)

| Step | Covered by |
|------|------------|
| Subscription lifecycle E2E | 018 K* tests |
| Invoice + MOCK payment | 019 L* tests |
| CRM → contract win | 017 J* tests |
| Full catalog-rights workflow | 021 N* tests |
| Playwright UI journey | automation/playwright (NOT_VERIFIED) |
| Docker full-stack smoke | infrastructure compose (NOT_VERIFIED) |

## Future spec candidates (informative only)

- 024 Royalties (requires 021 rights + warehouse $)
- 025 Payouts (requires 024 + banking)
- 029+ CS/Support/Exec report (if product prioritizes)

**028 does not authorize implementation of the above.**
