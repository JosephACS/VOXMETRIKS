# Spec 016 — I3 OrganizationContext

**Fecha:** 2026-07-11  
**Estado:** PASS

## Contenido

`user_id`, `organization_id`, `membership_id`, `membership_status`, `organization_status`, `role_codes`, `permission_codes`, `source`, `platform_role`, `request_id`.

## Precedencia

1. Path `{organization_id}`  
2. Else header `X-Organization-Id`  
3. Else preferencia `active_organization_id`  
4. Else `none`  

Path + header distintos → **400** `context_conflict`.  
Preferencia inválida/revocada → clear preference + `invalid` / `access_revoked`.  
Permisos siempre desde persistencia (roles active + mappings).
