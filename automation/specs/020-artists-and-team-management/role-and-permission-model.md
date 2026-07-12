# Role & Permission Model — Spec 020

## New permissions (domain: `artist`)
| Code | Description |
|---|---|
| `artist.view` | View artist profiles, team, assignments, history |
| `artist.create` | Create new artist profiles |
| `artist.update` | Update profile fields, link organizations, link warehouse artist |
| `artist.assign` | Assign/end managers, add/remove team members |
| `artist.archive` | Archive an artist profile |
| `artist.transfer` | Transfer artist to a different organization |

Defined in `app.packages.organizations.infrastructure.catalogs.PERMISSIONS`
and seeded into `app_permission` by `ensure_organization_tables` (same
mechanism as billing's `billing.*` permissions).

## Role grants (`ROLE_PERMISSION_MATRIX`)
| Role | artist.view | artist.create | artist.update | artist.assign | artist.archive | artist.transfer |
|---|---|---|---|---|---|---|
| owner | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| administrator | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| artist_manager | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| artist | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| viewer | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Enforcement
Every endpoint depends on
`require_org_artist_permission(<code>)` (in
`artists/presentation/dependencies.py`), which joins
`app_organization_member → app_member_role → app_business_role →
app_role_permission → app_permission` scoped by `X-Organization-Id` and the
authenticated `user_id` — identical shape to billing's
`require_org_billing_permission`. No new RBAC primitives were introduced.

## Test coverage
`test_organizations_schema_i1.py` verifies all 6 `artist.*` permissions are
seeded and correctly assigned per role (and removes `artist.view` from the
"future/banned" list, matching how `billing.view` was unbanned in spec 019).
`test_artists_security_m5.py` verifies a `viewer` gets 403 on create/assign
and 200 on list/view.
