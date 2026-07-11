# Spec 016 — I1 Repository validation

**Fecha:** 2026-07-11  
**Estado:** PASS (18 tests org)

## Repositorios

| Repo | Operaciones |
|------|-------------|
| OrganizationRepository | create, get_by_id, get_by_slug, list_for_user, update_basic_fields, update_status |
| MembershipRepository | create, get_by_id, get_by_org_and_user, list_by_organization, list_by_user, update_status (no DELETE físico) |
| InvitationRepository | create, get_by_id, get_by_token_hash, list_by_organization, find_active_by_org_and_email, update_status |
| AuthorizationRepository | list_member_roles, assign_member_role, revoke_member_role, list_role_permissions, member_has_permission |
| PreferenceRepository | get_for_user, set_active_organization, clear_active_organization |
| AuditRepository | append, list_by_organization (paginado); update/delete → error |

## Pruebas

`tests/test_organizations_schema_i1.py` + `tests/test_organizations_repositories_i1.py` → **18 PASS** (`_i1_pytest_orgs.txt`)

Cubre: CRUD org, filtros por `organization_id`, list_for_user, invitation hash/email, assign/revoke, member_has_permission, preferencia, audit append/paginación/no update-delete, aislamiento cross-org en listados SQL.
