> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** .specify/history/README.md; .specify/history/047-repository-recovery-hardening/spec.md + closure.md; docs/STATUS.md; código/pruebas actuales; git: 1d443907, fbf31a33, 73370fc3, d2f6a27f, 2c8d489b, 8a46d05e, 153e77f8, bb7b93bd
>
> Aviso visible: el documento original de esta Spec **no está disponible** en el historial Git consolidado.
> Esta carpeta reconstruye intención y resultado a partir de índices, Spec 047, STATUS y commits posteriores.
> No afirmar completitud solo porque existió la Spec. docs/STATUS.md y el runtime actual mandan.


# Spec 041 — Repository Structure & Spec Cleanup

**ID:** 041  
**Title:** Estructura del repositorio y limpieza de specs / Repository Structure & Spec Cleanup  
**Status:** HISTORICAL_RECONSTRUCTED  

## Objetivo histórico reconstruido

Ordenar estructura del monorepo y gobernanza Spec Kit (features vs history).

## Actores

Engineer / maintainers

## Alcance

.specify layout; docs consolidation; evitar automation/specs como canónico.

## Fuera de alcance

Recuperar automation/specs completo en el working tree.

## Reglas de negocio demostrables

- features/ solo activas.
- history/ cerradas.
- IDs inmutables.

## Casos de uso recuperables

1. Ubicar spec activa.
2. Consultar history.
3. DryRun siguiente ID.

## Criterios de aceptación verificables

- 2c8d489b docs consolidation.
- Este recovery 001–047 en history.

## Incertidumbres explícitas

- Detalle tareas 041 originales.
