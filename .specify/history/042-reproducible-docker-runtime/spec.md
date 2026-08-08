> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** .specify/history/README.md; .specify/history/047-repository-recovery-hardening/spec.md + closure.md; docs/STATUS.md; código/pruebas actuales; git: 1d443907, fbf31a33, 73370fc3, d2f6a27f, 2c8d489b, 8a46d05e, 153e77f8, bb7b93bd
>
> Aviso visible: el documento original de esta Spec **no está disponible** en el historial Git consolidado.
> Esta carpeta reconstruye intención y resultado a partir de índices, Spec 047, STATUS y commits posteriores.
> No afirmar completitud solo porque existió la Spec. docs/STATUS.md y el runtime actual mandan.


# Spec 042 — Reproducible Docker Runtime

**ID:** 042  
**Title:** Docker reproducible runtime / Reproducible Docker Runtime  
**Status:** HISTORICAL_RECONSTRUCTED  

## Objetivo histórico reconstruido

Runtime reproducible vía Compose canónico en raíz.

## Actores

Engineer

## Alcance

compose.yml backend+frontend; pipeline make; higiene runtime.

## Fuera de alcance

Obligatoriedad de Docker en todos los hosts; K8s.

## Reglas de negocio demostrables

- Compose canónico en raíz.
- Docker opcional si no está en PATH (STATUS).

## Casos de uso recuperables

1. docker compose up --build.
2. Demo local documentada.

## Criterios de aceptación verificables

- compose.yml presente.
- d2f6a27f runtime hygiene.
- STATUS Docker gate.

## Incertidumbres explícitas

- Matrices exactas de healthchecks originales.
