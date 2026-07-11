# Spec 016 — Cross-document validation

**Fecha:** 2026-07-11  
**Resultado:** Contradicciones documentales corregidas; diseño coherente para implementación

## Inconsistencias encontradas

| ID | Hallazgo | Resolución |
|----|----------|------------|
| C1 | Contexto org sin estados none/invalid/access_revoked ni precedencia path/header/pref | `organization-context-model.md` reescrito |
| C2 | Transiciones lifecycle incompletas / ambiguas (closed→active) | `lifecycle-state-machines.md` |
| C3 | Creación org sin atomicidad anti-huérfanos / idempotencia | organization-domain-model |
| C4 | Invitaciones: casos email mismatch, concurrente, resend, modo académico | membership-and-invitation-model |
| C5 | Logout no listado explícitamente en assessment | assessment actualizado (verificado en código) |
| C6 | DELETE member ambiguo vs soft remove | API usa POST …/remove |
| C7 | Custom roles no explicitados como OOS v1 | decisión C + role model |
| C8 | Aislamiento “filtrar en Python” no prohibido explícito | tenant-isolation-model |

## Validados

- Identity reutilizada; no JWT; no segundo login  
- 4 máquinas / 28 transiciones  
- Propiedad identity vs organizations  
- Matriz roles/permisos + futuros marcados  
- 18 contratos API  
- FE flows sin billing/CRM  
- Migración sin orgs ficticias  
- Trazabilidad US/FR → pruebas  

## No son bugs de diseño

SHA-256 passwords (deuda previa); Playwright opcional (deuda 014); email real diferido.
