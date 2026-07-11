# Spec 016 — I0 Mecanismo canónico de migración

**Fecha:** 2026-07-11  
**Decisión I0:** identificada; **no ejecutada** creación de tablas org en I0.

## Decisión

| Criterio | Elección |
|----------|----------|
| Mecanismo | Extender el bootstrap APP existente: función idempotente `ensure_organization_tables(conn)` (nombre previsto) en `packages/organizations/` (paquete nuevo en **I1**) |
| Invocación | Lifespan `main.py`, **junto a** `ensure_user_tables` / `ensure_app_tables`, **antes** de `mark_schema_ready()` |
| Guard | Respetar `schema_ready()` / patrón actual (DDL una vez por proceso tras boot) |
| DDL | `CREATE TABLE IF NOT EXISTS` + `ALTER` aditivo; **sin** DROP destructivo; **sin** regenerar warehouse |
| SQL disperso | **Prohibido** — un solo módulo de storage org |
| Seeds roles/permisos | En I1 tras DDL, idempotentes; **no** seeds de orgs “reales” ni backfill de miembros |
| Constitución 2.0.0 | DuckDB académico; reproducibilidad; no afirmar OLTP SaaS definitivo |
| Warehouse | **No** tocar `dim_*` / `fact_*` en 016 |

## Por qué este mecanismo

Coincide con identity (`user_storage.ensure_user_tables`), es idempotente, reproducible en arranque API, compatible DuckDB, y evita migraciones SQL sueltas o rebuild completo.

## Incorporación futura de tablas (I1, no I0)

1. `app_organization`
2. `app_organization_member`
3. `app_organization_invitation`
4. `app_business_role`
5. `app_permission`
6. `app_role_permission`
7. `app_member_role`
8. `app_user_organization_preference`
9. `app_audit_log`

## Scaffolding en I0

**No incluido.** La autorización humana de I0 es preparación/baseline. El scaffolding DDL comienza en **I1**.

## Rollback lógico (I1+)

Desactivar rutas/feature flag org; dejar tablas; sesiones identity intactas (ver `migration-and-compatibility.md`).
