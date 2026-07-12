# Deferred/Accepted Debt — Spec 028 (post email + mock payment integration)

## Accepted debt (external only)

| ID | Debt |
|----|------|
| X-01 | Playwright enterprise E2E NOT_VERIFIED |
| X-02 | Docker compose gate NOT_VERIFIED |
| X-03 | DuckDB academic concurrency limits |
| X-04 | No GDPR certification / licenses |
| X-05 | **Mock payment** only (`academic_mock`) — labeled, never real money |
| X-06 | Runtime ETL partial |
| X-07 | Royalties/Payouts OUT_OF_SCOPE |

## Removed from deferred (now implemented)

- Executive reporting (024)
- Customer Success / Support (025)
- Full pytest suite blocked by DuckDB lock / fixture pollution
- CRM → plan → subscription handoff (explicit selection)
- Billing dunning / mora + access recovery
- Calculable Active MRR / Past-due MRR / ARR (no FX)
- EmailPort providers (`console` / `smtp` / `resend`) + transactional templates
- Registration verification, resend (rate-limited), password reset
- Organization invitation email delivery status
- Billing / dunning / support / report-ready notifications (best-effort)
- Mock payment scenario simulator (demo/dev only)
- **Real SMTP smoke PASS** (`scripts/email_smtp_smoke.py`) — mock-email debt removed

## Out of scope (honest)

- Royalties / payouts (future specs — **not** numbered 024/025)
- Contractual SLA guarantees
- Spec 029
- Real payment gateway (money movement)
- PostgreSQL / HA production posture

## Acceptance

System remains **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT**. Remaining debt is external/environmental only.
Mock-email debt removed after real SMTP smoke PASS. Mock payment remains labeled debt.
