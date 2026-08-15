# Data Model — 053 Professional Organization Journey

## New metadata

### `app_organization_onboarding`

| Column | Purpose |
|---|---|
| `organization_id` | Logical primary key and tenant scope |
| `status` | `in_progress` or `completed` |
| `team_step_skipped_at` | Optional explicit owner choice |
| `completed_by` | User who completed the journey |
| `completed_at` | Durable completion time |
| `created_at`, `updated_at` | Audit timestamps |

This table stores no copied plan, payment, membership, permission, profile or access-tier state.

## Reused authorities

- `app_organization`: business profile and lifecycle.
- `app_organization_membership`, role/permission tables: access and team.
- `app_organization_invitation`: invitation lifecycle.
- Subscription and Billing tables: plan, checkout, invoice, payment and entitlement truth.
- Session/bootstrap preferences: active space and post-auth continuation.

## Derived journey state

`completed_steps`, `next_action` and capabilities are computed from current authoritative rows. The response can be cached only within a request; it is not materialized as a second source of truth.

## Catalogs

Organization type, country, timezone and currency must use a shared server-owned catalog. Country defaults may suggest timezone/currency; authorized users can select another supported value in advanced settings.
