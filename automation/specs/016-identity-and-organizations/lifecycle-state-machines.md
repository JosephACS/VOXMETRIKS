# Lifecycle State Machines — Spec 016

**Status**: DESIGN_APPROVED  
**Fecha**: 2026-07-11  

Cada transición: origen · acción · actor · precondición · destino · evento · auditoría · notificación · operación prohibida · HTTP tipico

---

## 1. Organization

Estados: `provisioning` · `active` · `suspended_by_platform` · `closed`

| Origen | Acción | Actor | Precondición | Destino | Evento | Audit | Notif | Prohibido | HTTP fail |
|--------|--------|-------|--------------|---------|--------|-------|-------|-----------|-----------|
| — | create | authenticated user | slug único; display_name válido | provisioning | OrganizationProvisioned | sí | — | crear sin auth | 401/409 slug |
| provisioning | activate | system (tx) | owner membership+role OK | active | OrganizationActivated | sí | — | activate sin owner | 500/rollback |
| active | suspend_platform | platform_admin/security | reason | suspended_by_platform | OrganizationSuspendedByPlatform | sí | owners | suspender por mora billing | 403 |
| suspended_by_platform | reinstate | platform_admin | review | active | OrganizationReinstated | sí | owners | reinstate sin reason | 403 |
| active | close | owner | confirm; no hard delete | closed | OrganizationClosed | sí | members | close=delete | 403 |
| suspended_by_platform | close | platform_admin/owner* | policy | closed | OrganizationClosed | sí | — | — | 403 |
| closed | * | * | — | — | — | — | — | **volver a active sin regla explícita** | 409 |
| closed | reopen | platform_admin + dual | **solo si se aprueba regla futura** | active | OrganizationReopened | sí | — | reopen por owner solo | 403 |

\* owner close desde suspended: solo si policy lo permite; default = platform_admin.

**Mutaciones de negocio en `closed` o `suspended_by_platform`:** denegadas para miembros (excepto lectura limitada / platform).

---

## 2. Organization member

Estados: `active` · `suspended` · `left` · `removed`

| Origen | Acción | Actor | Precondición | Destino | Evento | Audit | Notif | Prohibido | HTTP |
|--------|--------|-------|--------------|---------|--------|-------|-------|-----------|------|
| — | join_via_create | system | org create tx | active | MemberJoined | sí | — | org sin owner | — |
| — | join_via_invite | invitee | invite pending válida | active | MemberJoined | sí | admin | duplicate membership | 409 |
| active | suspend | admin/owner | not last owner | suspended | MemberSuspended | sí | member | suspend last owner | 409 |
| suspended | unsuspend | admin/owner | org active | active | MemberUnsuspended | sí | member | — | 403 |
| active | leave | self | not last owner | left | MemberLeft | sí | admin | leave as last owner | 409 |
| active | remove | admin/owner | not last owner | removed | MemberRemoved | sí | member | remove last owner; hard delete | 409 |
| suspended | remove | admin/owner | not last owner | removed | MemberRemoved | sí | — | — | — |
| left/removed | * | * | — | — | — | — | — | reutilizar fila como active sin flujo rejoin/invite | 409 |

`removed`/`left` ≠ borrado físico. Reingreso = nueva invite o flujo rejoin explícito (futuro).

---

## 3. Invitation

Estados: `pending` · `accepted` · `expired` · `revoked`

| Origen | Acción | Actor | Precondición | Destino | Evento | Audit | Notif | Prohibido | HTTP |
|--------|--------|-------|--------------|---------|--------|-------|-------|-----------|------|
| — | create | member+invite perm | org active; email norm; roles válidos | pending | MemberInvited | sí | academic/port | create si org closed/suspended | 403/409 |
| pending | accept | authenticated invitee | token hash match; not expired; email policy | accepted | InviteAccepted | sí | — | reuse token; accept revoked | 410/409 |
| pending | expire | system | past expires_at | expired | InviteExpired | sí | — | accept expired | 410 |
| pending | revoke | inviter/admin | — | revoked | InviteRevoked | sí | — | accept revoked | 409 |
| pending | resend | inviter/admin | org active | pending (new token_hash) | InviteResent | sí | academic | leave old token válido | — |
| accepted | * | * | — | — | — | — | — | reutilizar | 410 |

**Resend:** invalida token anterior (revoke lógico o rotate hash) — una pending activa por (org, email).

**Email ≠ usuario autenticado al accept:** 403 salvo política “accept for self email only” (aprobada: debe coincidir email normalizado del user autenticado).

---

## 4. Organization context

Estados lógicos: `none` · `active` · `invalid` · `access_revoked`

| Origen | Acción | Actor | Precondición | Destino | Evento | Audit | Notif | Prohibido |
|--------|--------|-------|--------------|---------|--------|-------|-------|-----------|
| none | activate | user | membership active; org active | active | OrganizationContextActivated | sí | — | activate sin membership |
| active | switch | user | membership OK en target | active (otra) | OrganizationContextActivated | sí | — | dos fuentes contradictorias sin regla |
| active | clear | user/system | — | none | OrganizationContextCleared | no/opcional | — | — |
| active | membership_suspended | system | — | access_revoked | OrganizationContextRevoked | sí | — | seguir usando preferencia ciega |
| active | org_closed/suspended | system | — | invalid | OrganizationContextInvalidated | sí | — | — |
| invalid / access_revoked | clear/resolve | system | — | none | — | — | — | ejecutar use-case org-scoped |

---

## Conteos

| Máquina | Transiciones documentadas |
|---------|--------------------------:|
| Organization | 8 |
| Member | 8 |
| Invitation | 6 |
| Context | 6 |
| **Total** | **28** |
