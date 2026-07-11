# Organization Domain Model — Spec 016

**Status**: DESIGN_APPROVED  
**Dominio propietario:** organizations  
**Owner inicial:** creador autenticado (decisión F)

---

## Ciclo de vida

Ver transiciones completas en `lifecycle-state-machines.md`.

Estados: `provisioning` · `active` · `suspended_by_platform` · `closed`  
**closed → active** prohibido sin regla explícita futura (platform dual).

## Campos

id · display_name · legal_name? · slug (**único global**) · organization_type · country_code? · timezone · default_currency · status · created_by · created_at · updated_at · closed_at? · is_demo? (seed only)

Sin billing_profile / datos fiscales completos.

## Creación atómica (flujo completo)

```text
usuario autenticado
→ POST /organizations (Idempotency-Key recomendada)
→ validar display_name + slug único
→ BEGIN TX lógica
   → insert organization status=provisioning
   → insert membership owner active
   → insert member_role owner
   → opcional: set preferencia contexto activo
   → update organization status=active
→ COMMIT
→ OrganizationProvisioned + OrganizationActivated + MemberJoined
→ audit
→ response
```

### Atomicidad / anti-huérfanos

| Fallo | Acción |
|-------|--------|
| slug conflict | no insert; 409 |
| membership fail | rollback org |
| role assign fail | rollback org+member |
| retry misma Idempotency-Key | devolver mismo resultado; no duplicar |
| retry sin key + mismo slug | 409 |

**Invariant:** no puede existir organization `active`/`provisioning` persistida sin ≥1 owner active + role owner.

## Reglas

| ID | Regla |
|----|-------|
| BR-ORG-016-01 | slug único global |
| BR-ORG-016-02 | ≥1 owner active |
| BR-ORG-016-03 | no retirar último owner |
| BR-ORG-016-04 | closed: no mutaciones miembro |
| BR-ORG-016-05 | suspended_by_platform: bloquea sensibles |
| BR-ORG-016-06 | close = lógico; no hard delete |
| BR-ORG-016-07 | transiciones auditadas |
| BR-ORG-016-08 | creación atómica anti-huérfanos |
| BR-ORG-016-09 | demo solo seed explícito (`is_demo`) |

## CRUD ownership

| Acción | Quién |
|--------|-------|
| create | cualquier authenticated (límites futuros rate-limit) |
| read | members con organization.view; platform elevated auditado |
| update | organization.update |
| status platform suspend | platform_admin/security |
| close | owner (organization.close) |
| audit read | audit.view |
