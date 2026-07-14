# Spec 029 — Personal Music Subscriptions

**Status:** CLOSED_WITH_ACCEPTED_DEBT  
**Date:** 2026-07-14  
**Owner type:** `user` (B2C) — never mixed with organization B2B (Spec 018)

## Summary

VOXMETRIKS offers two subscription lines:

| Line | Plans | Owner |
|------|-------|-------|
| B2C personal | Free, Premium Individual, Premium Duo, Premium Familiar | `user_id` |
| B2B enterprise | Starter, Professional, Business, Enterprise | `organization_id` |

A user may listen personally and also belong to organizations.

## User scenarios

1. Register → verify email → Free assigned → listen immediately  
2. Hit Free playlist/favorite limits → clear message + CTA to `/account/plans`  
3. Checkout Individual → mock payment succeeded → entitlements unlock  
4. Payment declined → Free access kept / Premium past_due + grace  
5. Duo invite member → second seat · third rejected  
6. Familiar up to 6 · seventh rejected  
7. Cancel / refund → members return to Free without deleting libraries  

## Functional requirements

- FR1 Separate personal tables (additive) from B2B  
- FR2 Canonical personal catalog with demo prices only in backend  
- FR3 Free on verify/login (no invoice)  
- FR4 Mock payment scenarios + personal invoices  
- FR5 Household Duo/Familiar with hashed single-use invites  
- FR6 Backend entitlement enforcement  
- FR7 Frontend `/account/*` (personal only)  
- FR8 Platform admin metrics B2C labeled separately from B2B  
- FR9 Opt-in demo seed · no passwords in repo · EMAIL_PROVIDER=console in tests  

## Assumptions

- No offline / HiFi / ad-free / exclusive content promises  
- Queue advanced = flag for clients; Free keeps basic queue  
- Grace period default 3 days  

## Success criteria

- Registration yields Free without org  
- Free limits blocked server-side  
- Premium activation unlocks limits  
- B2B golden path still green  
- Personal & enterprise catalogs never cross in UI/API lists  
