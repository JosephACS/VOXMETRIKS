# Spec 016 — I3 Error mapping

**Fecha:** 2026-07-11  
**Estado:** PASS

`presentation/error_mapping.py` → envelope `{status,message,details.code}`:

| Dominio | HTTP | code |
|---------|------|------|
| no auth (FastAPI dep) | 401 | — |
| PermissionDenied / email mismatch / org not operational | 403 | permission_denied / email_mismatch / org_not_active |
| NotFound* | 404 | not_found |
| slug / last_owner / membership conflict | 409 | slug_taken / last_owner / already_member |
| invite expired/used/revoked | 410 | invite_* |
| ValidationError | 422 | validation_error |
| path/header conflict | 400 | context_conflict |

Sin HTTPException en domain/application.
