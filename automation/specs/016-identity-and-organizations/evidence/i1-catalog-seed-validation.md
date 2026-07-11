# Spec 016 — I1 Catalog seed validation

**Fecha:** 2026-07-11  
**Estado:** PASS

## Roles (`app_business_role` = 9)

owner · administrator · billing_manager · finance · artist_manager · marketing_manager · analyst · artist · viewer  

Todos `scope=organization`, `is_system=true`. **No** se migraron roles plataforma `user|admin|engineer`.

## Permisos (`app_permission` = 15)

organization.view / create / update / close  
member.view / invite / suspend / remove  
role.view / assign  
invitation.view / revoke  
audit.view  
analytics.view  
report.view  

**No sembrados (FUTURO):** billing.view, artist.view, campaign.view  

`organization.create` existe en catálogo **sin** mapping a roles org (acción pre-membership).

## Matriz `app_role_permission` (48 pares)

| Role | Permissions |
|------|-------------|
| owner | organization.view, update, close; member.*; role.*; invitation.view/revoke; audit.view; analytics.view; report.view |
| administrator | organization.view, update; member.*; role.*; invitation.view/revoke; audit.view; analytics.view; report.view |
| billing_manager | organization.view, member.view |
| finance | organization.view, member.view, audit.view, report.view |
| artist_manager | organization.view, member.view, analytics.view |
| marketing_manager | organization.view, member.view, analytics.view, report.view |
| analyst | organization.view, member.view, analytics.view, report.view |
| artist | organization.view |
| viewer | organization.view, member.view, analytics.view |

Seed: `ensure_organization_role_catalogs` — inserta faltantes, no duplica, no crea orgs/users.
