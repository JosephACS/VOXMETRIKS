# I4 — Final result

**Stage I4**: COMPLETE  
**I5–I6**: NOT STARTED  
**Spec 017**: NOT CREATED  
**Git**: no commands executed (user manages Source Control)

## Delivered

Angular Organizations package wired to I3 API:

- no-org state, create, selector, onboarding
- settings, members, invitations (academic token), accept, roles, audit
- guards + dedicated denied/suspended/closed pages
- unit tests + lint/build validation

## Backend

No contract changes. Re-ran `test_organizations_api_i3.py` PASS only.

## Warehouse

No permanent smoke against production warehouse in I4.

## Residual risks / debt

- Members list shows `user_id` only (API membership contract has no email/name join yet).
- Invitation list resend UI allows pending/revoked; backend rules remain authority.
- E2E org flows NOT_VERIFIED.
- Bundle budget warnings preexistentes.
- Path guard activates org on navigation (extra POST activate) — intentional for UX sync.
