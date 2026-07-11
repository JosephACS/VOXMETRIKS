# Spec 016 — Orden I1–I6 (confirmado en I0; no iniciado)

**Fecha:** 2026-07-11  

> Nota: `plan.md` histórico nombraba I0=schema. **Autorización 2026-07-11** redefine:
> **I0 = preparación** (esta etapa, COMPLETE); **I1 = esquema y persistencia**.  
> Secuencia equivalente a `implementation-readiness.md` (schema → deps/context → members/invites → RBAC → FE → isolation tests), renumerada I1–I6.

| Etapa | Objetivo | Archivos esperados (previstos) | Dependencias | Pruebas | Criterio de detención | Rollback lógico | Evidencia |
|-------|----------|--------------------------------|--------------|---------|----------------------|-----------------|-----------|
| **I1** | Esquema y persistencia `app_organization*` + catálogos + preferencia + audit; seeds roles/permisos idempotentes; **sin** inventar orgs reales | `packages/organizations/services/*_storage.py`; llamada desde `main.py`; tests schema | I0 | pytest schema exists / idempotent ensure | Tablas creadas; identity intacta (5 users); sin endpoints org | Dejar tablas; no DROP; flag off | `evidence/i1-*` |
| **I2** | Dominio, reglas, casos de uso (create org atómico, membership, invitation rules, last-owner) | domain/services use-cases org; sin FE | I1 | unit domain / service | Reglas BR-* cubiertas en servicio | Revert servicios; DB queda | `evidence/i2-*` |
| **I3** | API (~18), permisos enforce, `OrganizationContext`, precedence path>header>preference | routes org; deps context; auth reuse | I2 | API tests + permission matrix | Contratos api-contracts; deny default | Desactivar router | `evidence/i3-*` |
| **I4** | Frontend + onboarding (selector org, guards UX, flujos invite) | `packages/organizations` FE; rutas; AuthService extend | I3 | unit FE | Flujos frontend-flows; rutas personales intactas | Ocultar UI org | `evidence/i4-*` |
| **I5** | Aislamiento tenant, auditoría elevada, compatibilidad no-org | filtros SQL; audit writes; cross-tenant tests | I3–I4 | cross-tenant + audit assertions | Sin leak cross-org; users sin org OK | Feature flag + leave tables | `evidence/i5-*` |
| **I6** | Validación integral y cierre documental | evidencias finales; checklist I | I1–I5 | pytest + FE + smokes | Criterios spec; estado diseño≠IMPLEMENTED hasta cierre | N/A cierre | `evidence/i6-*` |

## Estado al cierre de I0

- I0: **COMPLETE**
- I1–I6: **NOT STARTED**
