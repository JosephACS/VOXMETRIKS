# Traceability — Spec 016

**Status**: DESIGN_APPROVED · **IMPLEMENTATION_COMPLETE** · **CLOSED_WITH_ACCEPTED_DEBT**  
Cierre: `evidence/spec-closure.md`

## Cadena (as-implemented)

```text
015 producto B2B
  → capacidad Identity & Organizations (016)
    → procesos: create org, invite, membership, roles, context, audit
      → actores: authenticated user, org member, owner, invitee
        → CU US1–US7
          → reglas: deny-by-default, last-owner, anti-enum 404, invite single-use
            → estados: org/member/invite lifecycles
              → entidades app_organization*
                → repos packages/organizations/infrastructure
                  → endpoints /api/v1/organizations* + /invitations/{token}/accept
                    → pantallas packages/organizations (FE)
                      → permisos catalogs.py matrix
                        → pruebas I1–I5 + FE unit
                          → evidencia i0–i6
```

## Labels

| Área | Label |
|------|-------|
| Core org/identity | IMPLEMENTED |
| Email delivery | PARTIAL (academic not_sent) |
| Deny-audit | PARTIAL / DEFERRED |
| Playwright | NOT_VERIFIED |
| CRM/billing/… | OUT_OF_SCOPE |
| Platform elevation HTTP | DEFERRED |

## Sin huecos críticos

Endpoints api-contracts mapean a CU. Pantallas frontend-flows tienen endpoints. Permisos tienen roles. Tablas tienen proceso. Reglas tienen pruebas I2/I5. Criterios con evidencia i6.
