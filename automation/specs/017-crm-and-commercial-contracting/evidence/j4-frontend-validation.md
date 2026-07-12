# J4 — Frontend validation

**Status**: PASS (with accepted budget warnings)

## Package
`apps/frontend/src/app/packages/crm/`

Pages: dashboard, prospects list/detail, opportunity board/detail, quotation editor, approvals, contract detail, conversion wizard, lost opportunity, audit, access-denied.

Wired: `CRM_ROUTES` in `app.routes.ts` · nav section in dashboard layout · i18n en/es keys.

## Gates

| Gate | Result |
|------|--------|
| lint | **0 errors**, 14 warnings (preexisting + minor) |
| unit tests | **111 PASS** / 15 files (includes crm-j4) |
| build | **PASS** |
| budget | WARN initial 656.29 > 550 kB; home.css (preexisting debt) |

## Rules observed
- No claim token in localStorage
- Academic acceptance labeled (not legal certified signature)
- No billing UI
- Backend remains authz authority
