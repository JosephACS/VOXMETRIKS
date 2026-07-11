# Data Model (conceptual) — Spec 016

**Status**: DESIGN_APPROVED — **sin SQL**  
**Nombres candidatos confirmados documentalmente** (decisión implementación: usar estos nombres salvo conflicto técnico)

---

## Propiedad de dominio

| Entidad / tabla | Dominio propietario |
|-----------------|---------------------|
| app_user, app_session, app_email_code | **identity** |
| app_organization, app_organization_member, app_organization_invitation, app_member_role, app_user_organization_preference | **organizations** |
| app_business_role, app_permission, app_role_permission | **organizations** (catálogo sistema; seed global) |
| app_audit_log | **organizations** escribe org events; lectura compliance/audit.view; platform events org_id null |

Sin copropiedad ambigua: identity no escribe membership; organizations no muta password_hash.

---

## Restricciones por tabla

### app_organization
PK id · UNIQUE slug · FK created_by→app_user · CHECK status ∈ lifecycle · INDEX(status) · timestamps · closed_at? · is_demo bool default false · soft close via status

### app_organization_member
PK id · UNIQUE(organization_id, user_id) · FK org, user · CHECK status · timestamps de estado · **no DELETE físico**

### app_organization_invitation
PK id · FK org, invited_by · UNIQUE(token_hash) · INDEX(organization_id, email_normalized, status) · partial unique pending(org,email) — conceptual · expires_at NOT NULL

### app_business_role
PK code · system catalog fijo v1 (custom roles OOS)

### app_permission
PK code · includes reserved future codes marked future

### app_role_permission
PK (role_code, permission_code) · UNIQUE pair

### app_member_role
PK id · UNIQUE(member_id, role_code) · FK member, role

### app_user_organization_preference
PK user_id · FK last_organization_id nullable → app_organization · UNIQUE per user

### app_audit_log
PK audit_id · FK org nullable, actor_user_id · append-only · INDEX(org, occurred_at) · **no UPDATE/DELETE** por admin común

---

## Regla transaccional último owner

Al suspend/remove/leave: COUNT owners active en org MUST ≥ 1 tras operación; else abort 409.

## Retención / sensibilidad

| Tabla | Sensibilidad | Retención |
|-------|--------------|-----------|
| invitation email | media | hasta expire+grace |
| token_hash | alta | mientras pending |
| audit | alta | compliance policy |
| preference | baja | mientras user |
