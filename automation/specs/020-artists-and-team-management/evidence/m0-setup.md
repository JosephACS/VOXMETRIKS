# M0 Setup — Spec 020

**Status at M0:** IMPLEMENTATION_PENDING

## Context gathered before implementation
- Explored `apps/backend/app/packages/billing/` in full (domain/application/
  infrastructure/presentation layers) as the pattern to replicate for
  `artists`.
- Confirmed `/api/v1/artists` (GET/POST list + `/artists/{id}`) is already
  served by the legacy analytics/streaming catalog router — decided to
  mount the new business router under `/api/v1/artist-profiles` instead
  (see plan.md decision #1).
- Confirmed the frontend already has `/artists` and `/artists/:id` routes
  for the same legacy catalog feature — decided to mount the new business
  pages under `/artist-profiles` for the same reason.
- Confirmed `app_role_permission` (not `app_business_role_permission`) is
  the correct join table for permission checks, matching billing's
  dependencies.py.

## Plan for M1–M6
See `plan.md` milestones.
