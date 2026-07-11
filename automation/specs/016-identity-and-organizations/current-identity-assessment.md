# Current Identity Assessment — Spec 016

**Status**: DESIGN_APPROVED (assessment verificado vs código 2026-07-11)  
**Evidencia:** `apps/backend/app/packages/identity/`

---

## Inventario verificado

| Componente | Evidencia | Clasificación |
|------------|-----------|---------------|
| `app_user` | `user_storage.ensure_user_tables` | **Reutilizable** |
| `app_session` | token PK, user_id, expires | **Reutilizable** |
| `app_email_code` | verify codes hashed | **Reutilizable** |
| Auth Bearer | `Authorization: Bearer` → session lookup (`auth_deps`) | **Reutilizable** — **no es JWT** |
| Login / register | `routes/users.py` | **Reutilizable** |
| Verificación email | `verify_email`, resend | **Reutilizable** |
| Logout | `POST /api/v1/users/logout` invalida token (`revoke_session`) | **Reutilizable** |
| Perfil / preferences | `get_me`, update preferences | **Reutilizable** |
| Roles técnicos | `app_user.role` ∈ user/admin/engineer | **Legacy compatible** (plataforma) |
| `require_user_id` / admin / engineer | auth_deps | **Reutilizable** + adaptar org deps |
| FE auth + logout | `auth.service.ts`, layout logout | **Requiere adaptación** (org context) |
| Google login | existe en routes | **Legacy compatible** — fuera de cambio 016 salvo no romper |
| Organizations | no existe | **Objeto 016** |

---

## Confirmaciones de diseño

| Afirmación | Veredicto |
|------------|-----------|
| Reutiliza identity existente | **Sí** |
| No diseña segundo login | **Sí** |
| No llama JWT al bearer actual | **Sí** (corregido/explicitado) |
| No invalida sesiones al migrar schema | **Sí** (migración) |
| Roles técnicos ≠ roles org | **Sí** |
| Identidad global ≠ membership | **Sí** |

## Recuperación de contraseña

No verificada como flujo completo en este assessment → **pendiente / fuera del núcleo 016** salvo no romper endpoints existentes.

## Riesgos

SHA-256 passwords (deuda Constitución); DuckDB concurrency; confusión role técnico vs org.
