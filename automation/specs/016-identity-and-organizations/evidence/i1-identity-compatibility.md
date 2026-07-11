# Spec 016 — I1 Identity compatibility

**Fecha:** 2026-07-11  
**Estado:** PASS

## Row counts (warehouse real)

| Tabla | Antes (I0) | Después (I1) |
|-------|------------|--------------|
| app_user | 5 | **5** |
| app_session | 243 | **243** |
| app_email_code | 0 | **0** |
| app_organization | n/a | **0** |
| app_organization_member | n/a | **0** |

## Auth smoke

health 200 → login demo 200 → /me 200 → logout 200 → /me 401 (`_i1_auth_smoke.txt`)

Roles técnicos `user|admin|engineer` intactos. Sin membership automática. Usuarios sin org permitidos.

## Contratos

Login / logout / /me / bearer **sin cambios**.
