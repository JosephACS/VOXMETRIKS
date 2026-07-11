# Spec 016 — Implementation readiness

**Fecha:** 2026-07-11 (actualizado post-I0)

## Veredicto

# READY_FOR_IMPLEMENTATION

El diseño documental está **DESIGN_APPROVED**.  
**I0–I2 COMPLETE**.  
**I3 (API, autorización y contexto) COMPLETE** — ver `evidence/i3-*.md`.  
Siguiente: **I4 — frontend** (requiere autorización).

## Bloqueadores

**Ningún bloqueador de diseño estructural.**

## No-bloqueadores (conocidos)

| Ítem | Tipo |
|------|------|
| Email real / NotificationPort | Diferido — modo académico OK |
| Password SHA-256 | Deuda seguridad previa |
| Playwright e2e | Deuda 014 — API/unit primero; CLI disponible, no e2e en I0 |
| feature.json → 016 | **Hecho en I0** |
| Docker | NOT_AVAILABLE en entorno I0 |
| Reopen closed org | Diferido |

## Orden de implementación (canónico post-autorización)

| # | Etapa | Estado |
|---|-------|--------|
| I0 | Prep + baseline + activación | **COMPLETE** |
| I1 | Schema `app_organization*` + seeds catálogo | **COMPLETE** |
| I2 | Dominio / reglas / casos de uso | **COMPLETE** |
| I3 | API + permisos + OrganizationContext | **COMPLETE** |
| I4 | FE + onboarding | NOT STARTED |
| I5 | Aislamiento + auditoría + compatibilidad | NOT STARTED |
| I6 | Validación integral y cierre | NOT STARTED |

Equivalente histórico readiness: schema → context/APIs → members/invites → RBAC → FE → isolation tests.

## Prohibido hasta nueva autorización (I1+)

Mutar DuckDB con tablas org · implementar endpoints/FE org · abrir 017 · tocar Constitución / TRACEABILITY-MASTER sin permiso · marcar IMPLEMENTED.
