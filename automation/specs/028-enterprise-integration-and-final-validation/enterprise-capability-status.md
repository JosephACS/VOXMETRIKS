# Enterprise Capability Status — Spec 028 (reopened 2026-07-12)

**Labels:** IMPLEMENTED | PARTIAL | DEFERRED | NOT_VERIFIED | OUT_OF_SCOPE

| Domain | Spec | Status | Evidence |
|--------|------|--------|----------|
| Repository stabilization | 014 | **IMPLEMENTED** | Monorepo, route policy, ELT canonical |
| Enterprise foundation (design) | 015 | **PARTIAL** | Design docs; capabilities now implemented via 016–028 |
| Identity & auth | 001/016 | **IMPLEMENTED** | `identity`, login, RBAC seeds |
| Organizations | 016 | **IMPLEMENTED** | `organizations` |
| Platform RBAC | 016/017 | **IMPLEMENTED** | `platform_rbac` |
| CRM | 017 | **IMPLEMENTED** | `crm` |
| Commercial contracts | 017 | **IMPLEMENTED** | `contracts` |
| Billing & reconciliation | 019 | **IMPLEMENTED** | `billing`, MOCK payment, dunning/mora |
| Plans & subscriptions | 018 | **IMPLEMENTED** | `subscriptions`, CRM plan handoff |
| Business analytics | 023 | **IMPLEMENTED** | `business_analytics`, Active/Past-due MRR/ARR |
| Integration validation | 028 | **IMPLEMENTED** | commercial golden path + gap closure |
| Royalties / payouts | — | **OUT_OF_SCOPE** | Future unnumbered specs; **not** 024/025 |
| Music streaming UX | 001–004 | **IMPLEMENTED** | Catalog, player, playlists |
| ELT / warehouse | 008/014 | **IMPLEMENTED** | `analytics/elt` |
| Runtime ETL | 014 | **PARTIAL** | Refresh only |
| Playback core V2 | 014 | **PARTIAL** | Proposed |
| Enterprise E2E (Playwright) | — | **NOT_VERIFIED** | |
| Docker compose gate | — | **NOT_VERIFIED** | |
| GDPR certification | — | **OUT_OF_SCOPE** | |

## Summary

- **IMPLEMENTED:** enterprise domains 016–027 including corrected 024/025
- **PARTIAL:** 015 design-only residual, runtime ETL, playback V2
- **OUT_OF_SCOPE:** royalties/payouts, GDPR cert, contractual SLA
- **NOT_VERIFIED:** Playwright enterprise, Docker CI gate
