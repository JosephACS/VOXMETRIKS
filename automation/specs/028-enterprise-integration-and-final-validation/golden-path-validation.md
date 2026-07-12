# Golden Path Validation — Spec 028

Maps the end-to-end enterprise journey and marks each step **VERIFIED** (pytest/API) or **DEFERRED**.

## Path diagram

```text
[Login] → [Org context] → [Plan catalog] → [Subscribe*] → [Bill*]
    → [CRM prospect*] → [Contract*] → [Artist profile*] → [Catalog rights*]
    → [Campaign] → [ROI*] → [Business analytics] → [Compliance terms]
    → [Platform ops health] → [Renewal/CS*] → [Executive report*]

* = partial or deferred in this closure
```

## Step matrix

| # | Step | API / UI | Status | Notes |
|---|------|----------|--------|-------|
| 1 | User login | `POST /api/v1/users/login` | **VERIFIED** | `test_enterprise_golden_path_s028` |
| 2 | List organizations | `GET /api/v1/organizations` | **VERIFIED** | Same test |
| 3 | Org context header | `X-Organization-Id` + `/organizations/current` | **VERIFIED** | Same test |
| 4 | List plans | `GET /api/v1/plans` | **VERIFIED** | platform_admin in test |
| 5 | Create subscription | `POST /api/v1/subscriptions` | **DEFERRED** | Covered in 018 tests, not golden chain |
| 6 | Issue invoice | `POST /api/v1/billing/invoices` | **DEFERRED** | 019 L* tests; not chained here |
| 7 | Payment (MOCK) | billing provider | **DEFERRED** | MOCK labeled; manual demo |
| 8 | CRM prospect | `POST /api/v1/crm/prospects` | **DEFERRED** | 017 J* tests exist |
| 9 | Commercial contract | `POST /api/v1/contracts` | **DEFERRED** | 017 tests exist |
| 10 | Artist profile | `POST /api/v1/artists` | **DEFERRED** | 020 M* tests |
| 11 | Catalog asset | `POST /api/v1/catalog-rights/assets` | **DEFERRED** | 021 N* tests |
| 12 | List campaigns | `GET /api/v1/campaigns` | **VERIFIED** | Golden path test |
| 13 | Campaign ROI | `POST /campaigns/{id}/roi` | **DEFERRED** | Honest unavailable states |
| 14 | Business analytics dashboard | `GET /business-analytics/dashboard` | **VERIFIED** | Golden path test |
| 15 | Compliance terms list | `GET /compliance/terms` | **VERIFIED** | Golden path test |
| 16 | Platform ops health | `GET /platform-ops/health` | **VERIFIED** | Golden path test |
| 17 | Customer success renewal | `/customer-success` | **DEFERRED** | 404 — not built |
| 18 | Support ticket | `/support` | **DEFERRED** | 404 — not built |
| 19 | Executive report | `/reporting/reports` | **DEFERRED** | 404 — not built |
| 20 | Royalties accrual | — | **DEFERRED** | Spec 024 NOT_PRESENT |
| 21 | Payout run | — | **DEFERRED** | Spec 025 NOT_PRESENT |
| 22 | Playwright E2E UI path | automation/playwright | **DEFERRED** | NOT_VERIFIED |
| 23 | Docker full stack | docker-compose | **DEFERRED** | NOT_VERIFIED in CI |

## Automated evidence

```bash
cd apps/backend
python -m pytest tests/test_enterprise_golden_path_s028.py -q
```

Deferred-domain assertions expect **404** for support, customer-success, and reporting/reports.
