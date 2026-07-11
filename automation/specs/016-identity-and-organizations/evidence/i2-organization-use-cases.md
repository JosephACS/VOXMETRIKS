# Spec 016 — I2 Organization use cases

**Fecha:** 2026-07-11  
**Estado:** PASS

## Casos

| Use case | Archivo |
|----------|---------|
| CreateOrganization | `use_cases/create_organization.py` |
| UpdateOrganizationProfile | `use_cases/organization_ops.py` |
| ChangeOrganizationStatus | `use_cases/organization_ops.py` |

## Create atómico

TX: provisioning org → membership owner → role owner → activate → preferencia opcional → audit.  
Rollback si falla role (probado). Sin org huérfana. `is_demo=false`.
