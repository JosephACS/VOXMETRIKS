# I5 — Tenant isolation

**Status**: COMPLETE

## Inventario organization-scoped (016 only)

| Recurso | Repo | UC | Endpoint | Filtro `organization_id` | Permiso | Auditoría |
|---------|------|----|----------|--------------------------|---------|-----------|
| Organization | `organization_repository` | create/update/status | POST/GET/PATCH/close | PK / list via membership | view/update/close | create/update/status |
| Membership | `membership_repository` | MembershipUseCases | members list/patch/remove | SQL WHERE org (+ UPDATE AND org) | member.* | suspend/reactivate/left/remove |
| Invitation | `invitation_repository` | InvitationUseCases | invitations CRUD-ish | SQL WHERE org | invite/view/revoke | create/accept/revoke/resend |
| Member roles | `authorization_repository` | RoleUseCases | PUT …/roles | member∈org (+ UPDATE JOIN org) | role.assign/view | assign/revoke |
| Preference | `preference_repository` | PreferenceUseCases | activate/current | user_id | active membership | changed/cleared |
| Audit | `audit_repository` | — | GET audit-log | SQL WHERE org + LIMIT | audit.view | N/A (read) |

Sin dominios futuros (billing/CRM/campaigns/artists).

## Hallazgos corregidos

1. UPDATE membership/invitation ahora exige `organization_id` en WHERE cuando se pasa desde UC.
2. Role mutate verifica member∈org y UPDATE con subquery org.
3. List invitations: ya no basta `member.view` (viewer); requiere `member.invite` | `invitation.view`.
4. Pagination members/invitations vía SQL LIMIT/OFFSET.
5. `NotFoundError` de repo → HTTP 404 (antes caía en OrganizationsError 400).
