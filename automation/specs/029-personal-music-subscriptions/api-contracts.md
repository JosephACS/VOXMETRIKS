# API contracts — Spec 029

Base: `/api/v1/personal`

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | /plans | public | Personal catalog only |
| GET | /subscription | user | Own subscription |
| GET | /entitlements | user | Limits |
| POST | /checkout | user | Creates invoice+attempt |
| POST | /payment-attempts/{id}/simulate | user | mock scenarios |
| POST | /subscription/cancel | user | |
| POST | /subscription/change-period | user | |
| POST | /subscription/refund | user | |
| GET | /invoices | user | |
| GET | /household | user | |
| POST | /household/invitations | owner | rate limited |
| POST | /household/invitations/{id}/cancel | owner | |
| POST | /household/accept | user | token once |
| POST | /household/members/{id}/remove | owner | |
| GET | /admin/metrics | ops.view | B2C + labeled B2B peek |
| GET | /admin/subscriptions | ops.view | |
| POST | /admin/demo-seed | ops.manage | opt-in |

Enterprise plans remain under `/api/v1/plans` + `/subscriptions` (org header).
