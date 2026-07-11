# Tenant Isolation Model — Spec 016

**Status**: DESIGN_APPROVED

## Exigencias

1. `organization_id` en entidades org-scoped  
2. Filtros en **repositorio/SQL** (no fetch global + filter Python)  
3. Use-cases reciben `OrganizationContext` validado  
4. Pertenencia validada aunque el ID exista  
5. Cross-tenant: **404** (anti-enum) salvo membership suspendida → **403**  
6. Platform elevated: explícito, reason, expiry, audit  
7. Pruebas seguridad listadas en test-strategy  

## DuckDB

Sin aislamiento multi-tenant nativo. Aislamiento = aplicación + tests. Límite académico (Constitución 2.0.0 / decisión J).
