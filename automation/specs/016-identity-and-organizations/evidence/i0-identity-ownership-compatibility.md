# Spec 016 — I0 Identity actual, ownership, compatibilidad, seguridad

**Fecha:** 2026-07-11  
**Estado:** CONFIRMADO contra código (sin mutaciones de contrato)

## 1. Identidad actual (código)

| Pregunta | Respuesta verificada |
|----------|----------------------|
| Definición `app_user` / `app_session` / `app_email_code` | `apps/backend/app/packages/identity/services/user_storage.py` → `ensure_user_tables` |
| Bearer token | UUID opaco en `create_session` → fila `app_session.token` (**no JWT**) |
| Validación sesión | `resolve_session` / `get_user_id_from_token` + `auth_deps.require_user_id` (Header Authorization Bearer) |
| Login | `POST /api/v1/users/login` — `packages/identity/routes/users.py` + `user_service` |
| Logout | `POST /api/v1/users/logout` — revoca token (`revoke_session`) |
| `/me` | `GET /api/v1/users/me` — `Depends(require_user_id)` |
| Verificación correo | `app_email_code` + flujos verify en `user_service` (hash de código, attempts, expires) |
| Roles técnicos | `user` \| `admin` \| `engineer` en `app_user.role` |
| Auth deps reutilizables por orgs | `require_user_id`, `require_admin_user`, `require_engineer_user`, `ensure_self_or_admin`, `get_optional_user_id` |
| FE consumidores | `AuthService` (`core/services/auth.service.ts`), `authGuard`/`guestGuard`/`engineerGuard`, login/settings/users, interceptors auth/catalog, varios servicios streaming/analytics |

**MUST:** no diseñar segundo sistema de autenticación. Login/logout/register/verify/perfil **sin cambio de contrato en I0** (ni iniciados en I1+ hasta su etapa).

## 2. Convenciones de nombres

Confirmadas (data-model.md + tablas APP existentes):

- Prefijo `app_` para tablas de aplicación (no warehouse `dim_`/`fact_`).
- Identity: `app_user`, `app_session`, `app_email_code`.
- Organizations (futuro I1): `app_organization`, `app_organization_member`, `app_organization_invitation`, `app_business_role`, `app_permission`, `app_role_permission`, `app_member_role`, `app_user_organization_preference`, `app_audit_log`.
- Sin inventar sinónimos (`orgs`, `tenant`, etc.) salvo conflicto técnico documentado.

## 3. Propiedad de datos (sin copropiedad)

| Dominio | Propietario de | No muta |
|---------|----------------|---------|
| **IDENTITY** | `app_user`, `app_session`, `app_email_code`; autenticación; credenciales; sesiones | membership, invitations, org RBAC |
| **ORGANIZATIONS** | organization, membership, invitation, member role assignment, org preference/context, auditoría organizacional; **único dueño** de catálogos globales `app_business_role` / `app_permission` / `app_role_permission` (seed sistema) | `password_hash`, emisión/revocación de session tokens |

## 4. Compatibilidad (plan confirmado; no implementado retiro modo personal)

- Conservar los **5** `app_user` actuales.
- Conservar sesiones actuales (schema add no debe invalidar tokens).
- Usuarios **sin** organización permitidos.
- **No** crear organizaciones ficticias automáticamente.
- **No** migrar usuarios a orgs sin acción explícita (crear / aceptar invitación / seed demo marcado `is_demo` + ENV).
- No romper roles `user`/`admin`/`engineer`.
- Mantener rutas actuales (`login`, `users`, `settings`, resto personal).
- Añadir organization context **sin** exigir org para funciones personales existentes.
- Retiro del modo personal: **fuera de I0–I6 cierre** salvo decisión futura explícita.

## 5. Seguridad previa (para I1+)

Usará:

- Dependencias de autenticación existentes (`auth_deps`).
- Deny by default en permisos org.
- Autorización **backend** (no confiar en Angular guards como control de acceso).
- `OrganizationContext` validado en servidor.
- Filtros SQL por `organization_id` (no post-hoc Python filter como única defensa).
- Pruebas cross-tenant.
- Auditoría de acceso elevado.

**No confiar en:** guards Angular solos; `organization_id` del cliente; preferencia guardada sin revalidación; roles enviados desde el frontend.

I0 **no** implementa acceso cross-org.
