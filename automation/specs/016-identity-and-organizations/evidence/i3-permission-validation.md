# Spec 016 — I3 Permission validation

**Fecha:** 2026-07-11  
**Estado:** PASS

- `require_organization_permission(code)` deny-by-default  
- Mutations requieren org `active`  
- Views permiten lectura con membership active aunque org no-active (403 org_not_active si status bloquea vía contexto)  
- owner ≠ platform_admin; rol técnico no da cross-org  
- PUT roles exige `role.assign`; viewer no asigna (probado)
