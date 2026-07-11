# Spec 016 — I2 Identity compatibility

**Fecha:** 2026-07-11  
**Estado:** PASS

| Tabla | Count |
|-------|------:|
| app_user | 5 |
| app_session | 243 |
| app_email_code | 0 |
| app_organization (warehouse) | 0 |
| app_organization_member | 0 |

Auth smoke: health → login → /me → logout → 401.  
Frontend / API pública sin cambios. Orgs solo en DB temporal de tests.
