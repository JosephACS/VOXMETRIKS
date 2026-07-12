# J6 — E2E validation

**Status**: **NOT_VERIFIED**

## Cause
Playwright config exists under `automation/playwright/` but **0** CRM (and org) `*.spec.ts` E2E specs are present for the golden path.

## Not claimed
PASS for browser E2E golden path.

## Compensating evidence
- Backend integration/security tests cover conversion, approvals, immutability, 403 isolation
- Frontend unit tests cover routes/guards/API client
- Full pytest + FE lint/unit/build PASS

Accepted as debt — see `accepted-debt.md`.
