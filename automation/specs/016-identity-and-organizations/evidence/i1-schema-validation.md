# Spec 016 — I1 Schema validation

**Fecha:** 2026-07-11  
**Estado:** PASS

## Mecanismo

- `ensure_organization_tables(conn)` en `packages/organizations/infrastructure/schema.py`
- Invocado en `main.py` lifespan junto a `ensure_user_tables` / `ensure_app_tables` (antes de `mark_schema_ready`)
- También en `tests/conftest.py` para DB de sesión de pytest
- Idempotente: `CREATE TABLE IF NOT EXISTS` + seed catalogs; errores de DDL org **no** se ocultan
- No ELT, no rebuild warehouse, no mutación de `app_user` / `app_session` / `app_email_code`

## Nueve tablas (warehouse real)

| Tabla | Columnas | Rows post-I1 |
|-------|----------|--------------|
| app_organization | 14 | 0 |
| app_organization_member | 11 | 0 |
| app_organization_invitation | 14 | 0 |
| app_business_role | 9 | 9 |
| app_permission | 7 | 15 |
| app_role_permission | 4 | 48 |
| app_member_role | 8 | 0 |
| app_user_organization_preference | 4 | 0 |
| app_audit_log | 14 | 0 |

Detalle columnas: `_i1_schema_describe.txt`

## Restricciones comprobadas

- UNIQUE slug / token_hash / (org,user) / (role_id,permission_id) / (member_id,role_id) / preference PK user_id
- CHECK status enums (org, member, invitation, member_role)
- CHECK closed_at solo con status=closed
- CHECK scope=organization en business_role
- Validación de estados inválidos en repositorio
- Duplicados rechazados (tests)

## Limitación DuckDB

No se indexa `status` mutable: ART no permite overwrite en UPDATE (Constraint Duplicate key). Índice invitation es `(organization_id, email_normalized)` sin `status`.
