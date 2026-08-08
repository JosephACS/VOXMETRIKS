> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** .specify/history/README.md; .specify/history/047-repository-recovery-hardening/spec.md + closure.md; docs/STATUS.md; código/pruebas actuales; git: 1d443907, fbf31a33, 73370fc3, d2f6a27f, 2c8d489b, 8a46d05e, 153e77f8, bb7b93bd
>
> Aviso visible: el documento original de esta Spec **no está disponible** en el historial Git consolidado.
> Esta carpeta reconstruye intención y resultado a partir de índices, Spec 047, STATUS y commits posteriores.
> No afirmar completitud solo porque existió la Spec. docs/STATUS.md y el runtime actual mandan.


# Spec 037 — Functional Security, Org Isolation & Catalog Cycle

**ID:** 037  
**Title:** Seguridad funcional, aislamiento org y ciclo de catálogo / Functional Security, Org Isolation & Catalog Cycle  
**Status:** HISTORICAL_RECONSTRUCTED  

## Objetivo histórico reconstruido

Endurecer aislamiento org-scoped y ciclo de catálogo/publicación con controles funcionales.

## Actores

Org members, platform admin, catalog operators

## Alcance

X-Organization-Id, 400/403 isolation, catalog rights/publishing basics, account security residual.

## Fuera de alcance

Certificación de seguridad formal; pentest.

## Reglas de negocio demostrables

- 400 sin header org cuando requerido.
- 403 org ajena.
- Refunds/security org-scoped donde aplique.

## Casos de uso recuperables

1. Acceder recurso con membresía.
2. Rechazo cross-org.
3. Ciclo catálogo básico.

## Criterios de aceptación verificables

- 047 closure: isolation gates.
- 73370fc3 enterprise reconciliation.
- 8a46d05e access coverage.

## Incertidumbres explícitas

- Lista exacta FR 037 no disponible.
