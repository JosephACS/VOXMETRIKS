> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** .specify/history/README.md; .specify/history/047-repository-recovery-hardening/spec.md + closure.md; docs/STATUS.md; código/pruebas actuales; git: 1d443907, fbf31a33, 73370fc3, d2f6a27f, 2c8d489b, 8a46d05e, 153e77f8, bb7b93bd
>
> Aviso visible: el documento original de esta Spec **no está disponible** en el historial Git consolidado.
> Esta carpeta reconstruye intención y resultado a partir de índices, Spec 047, STATUS y commits posteriores.
> No afirmar completitud solo porque existió la Spec. docs/STATUS.md y el runtime actual mandan.


# Spec 034 — Role-Based Navigation Simplification

**ID:** 034  
**Title:** Simplificación de navegación por roles / Role-Based Navigation Simplification  
**Status:** HISTORICAL_RECONSTRUCTED  

## Objetivo histórico reconstruido

Simplificar navegación según rol/espacio sin romper RBAC.

## Actores

Listener, artist-space member, org staff, platform admin

## Alcance

Chrome/nav por espacio; refinamientos 045/153e77f8/bb7b93bd.

## Fuera de alcance

Rediseño total de IA; nuevos roles de negocio no especificados.

## Reglas de negocio demostrables

- RBAC org-scoped intacto.
- Nav contextual no inventa permisos.

## Casos de uso recuperables

1. Cambiar espacio y ver nav coherente.
2. Ocultar paneles vacíos (p.ej. ops).

## Criterios de aceptación verificables

- 045 spaces navigation cerrado.
- Hardening presentation 153e77f8/bb7b93bd.

## Incertidumbres explícitas

- FR exactos 034 desconocidos; solape con 045.
