# Role and Permission Model — Spec 016

**Status**: DESIGN_APPROVED  
**Custom roles:** fuera de v1 (decisión C) — catálogo fijo.

## Separación

- Roles **organización** ≠ roles **plataforma** ≠ `app_user.role` técnico (compatibilidad).  
- **owner ≠ platform_admin**

## Roles org + matriz

Ver matriz en sección siguiente (misma que borrador, validada):

| Permiso | owner | admin | billing_mgr | finance | artist_mgr | mkt_mgr | analyst | artist | viewer |
|---------|:-----:|:-----:|:-----------:|:-------:|:----------:|:-------:|:-------:|:------:|:------:|
| organization.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| organization.update | ✓ | ✓ | | | | | | | |
| organization.close | ✓ | | | | | | | | |
| member.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| member.invite | ✓ | ✓ | | | | | | | |
| member.suspend | ✓ | ✓ | | | | | | | |
| member.remove | ✓ | ✓ | | | | | | | |
| role.view | ✓ | ✓ | | | | | | | |
| role.assign | ✓ | ✓ | | | | | | | |
| audit.view | ✓ | ✓ | | ✓ | | | | | |
| billing.view | ✓ | | ✓ | ✓ | | | | | | **FUTURO** |
| artist.view | ✓ | ✓ | | | ✓ | ✓ | ✓ | ✓* | | **FUTURO*** |
| campaign.view | ✓ | ✓ | | | | ✓ | ✓ | | | **FUTURO** |
| analytics.view | ✓ | ✓ | | | ✓ | ✓ | ✓ | | ✓ |
| report.view | ✓ | ✓ | | ✓ | | ✓ | ✓ | | |

\* artist: solo ámbito propio cuando exista dominio artists — hasta entonces permiso reservado no habilita módulo.

## Comprobaciones

| Regla | OK |
|-------|----|
| viewer no modifica | sí |
| billing_manager no role.assign / security | sí |
| finance no role.assign | sí |
| analyst no member.* mutaciones | sí |
| admin no elimina último owner | regla transaccional |
| cross-org solo plataforma + reason + audit | sí |
| deny by default / backend enforce | sí |

## Plataforma

sales_agent · sales_manager · customer_success_manager · support_agent · platform_finance · security_admin · platform_admin · auditor  

+ compat `admin`/`engineer` técnicos.
