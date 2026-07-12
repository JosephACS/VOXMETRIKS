# Accepted Debt — Spec 028

Consolidated debt at **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT**.

## Cross-cutting

| ID | Debt | Origin |
|----|------|--------|
| X-01 | Playwright enterprise E2E NOT_VERIFIED | 014+, all domain specs |
| X-02 | Docker compose gate NOT_VERIFIED | CI uses pytest only |
| X-03 | DuckDB academic concurrency limits | Architecture |
| X-04 | No GDPR certification | 026 |
| X-05 | MOCK payment/email only | 019, 027 |
| X-06 | Runtime ETL partial (not full ELT) | 014 |

## Domain-specific (carried forward)

| ID | Debt | Spec |
|----|------|------|
| D-016 | Playwright org flows | 016 |
| D-017 | CRM E2E NOT_VERIFIED | 017 |
| D-019 | `platform_finance` break-glass deferred | 019 |
| D-020 | No UnlinkWarehouseArtist; DELETE+INSERT mutations | 020 |
| D-021 | `valid_to` no auto-expire; no `dim_album` FK | 021 |
| D-022 | No FX conversion; ROI honest unavailable | 022 |
| D-023 | Trends/comparatives stubs; no AI recs | 023 |
| D-026 | No automated warehouse PII purge | 026 |
| D-027 | Conceptual backup; no production HA | 027 |

## Absent specs (not debt — explicit gap)

| Spec | Topic |
|------|-------|
| 024 | Royalties — NOT_PRESENT |
| 025 | Payouts — NOT_PRESENT |

## Deferred by design (015 → future)

| Topic | Status |
|-------|--------|
| Customer Success | DEFERRED — 028 forbids |
| Support | DEFERRED — 028 forbids |
| Executive reporting | DEFERRED — 028 forbids |

## Acceptance rationale

Debt items are documented, tested where feasible, and do not block academic closure. Production hardening requires specs beyond 028.
