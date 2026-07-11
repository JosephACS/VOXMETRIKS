# Organization Context Model — Spec 016

**Status**: DESIGN_APPROVED  
**Decisiones:** A, B (ver `evidence/approved-decisions.md`)

---

## Mecanismo único

**Fuente de verdad de preferencia:** `app_user_organization_preference.last_organization_id` (persistida).

**Validación:** en **cada** request organization-scoped la preferencia/header/path se **revalida** (membership active + org status). Nunca confiar ciegamente en valor guardado, body, Angular guard o header solo.

## Precedencia (una sola regla)

Para resolver `requested_org_id`:

1. **Path** `/organizations/{organization_id}/...` si presente  
2. Else **Header** `X-Organization-Id` si presente  
3. Else **preferencia persistida**  
4. Else → contexto `none`

Si path y header están ambos presentes y **difieren** → **400** (fuentes contradictorias).  
Body `organization_id` **MUST NOT** sobrescribir path/header; si viene y contradice → **400**.

## Estados de contexto

| Estado | Significado |
|--------|-------------|
| `none` | Sin org activa / usuario sin orgs |
| `active` | Org resuelta + membership active + org active |
| `invalid` | Preferencia apunta a org closed/inexistente |
| `access_revoked` | Membership suspended/left/removed |

Al detectar `invalid` o `access_revoked`: limpiar preferencia (o marcar stale) + **403/404** según política anti-enumeración documentada en API (default: **404** para IDs ajenos; **403** si membership existe pero suspendida).

## Pipeline obligatorio (org-scoped)

1. Autenticar (Bearer → user_id) → else **401**  
2. Resolver organización (precedencia) → else **403/404** si endpoint exige org  
3. Validar membresía **active**  
4. Validar estado organización (`active`; `suspended_by_platform`/`closed` → deny mutaciones)  
5. Validar permiso  
6. Ejecutar caso de uso  
7. Auditar si sensible  

## Casos

| Situación | Comportamiento |
|-----------|----------------|
| Una sola org | Auto-sugerir activate en onboarding; aún validar cada request |
| Cero orgs | contexto `none`; personal/demo OK; enterprise → onboarding |
| Switch | POST activate + audit |
| Suspended member | access_revoked; clear |
| Org closed | invalid; clear |

## Prohibido

- Confiar solo en FE  
- Preferencia sin revalidar  
- Dos fuentes contradictorias sin 400  
- Ejecutar use-case en `invalid`/`access_revoked`/`none` cuando se exige org
