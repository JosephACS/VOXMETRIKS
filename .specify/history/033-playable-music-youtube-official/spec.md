> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** .specify/history/README.md; .specify/history/047-repository-recovery-hardening/spec.md + closure.md; docs/STATUS.md; código/pruebas actuales; git: 1d443907, fbf31a33, 73370fc3, d2f6a27f, 2c8d489b, 8a46d05e, 153e77f8, bb7b93bd
>
> Aviso visible: el documento original de esta Spec **no está disponible** en el historial Git consolidado.
> Esta carpeta reconstruye intención y resultado a partir de índices, Spec 047, STATUS y commits posteriores.
> No afirmar completitud solo porque existió la Spec. docs/STATUS.md y el runtime actual mandan.


# Spec 033 — Playable Music + YouTube Official

**ID:** 033  
**Title:** Cierre del producto musical (playable + YouTube oficial) / Playable Music + YouTube Official  
**Status:** HISTORICAL_RECONSTRUCTED  

## Objetivo histórico reconstruido

Hacer reproducible el núcleo musical con resolver/player y contrato YouTube oficial aprobado.

## Actores

Listener, engineer

## Alcance

Playback-core, music player, Unified Music Search núcleo (posterior), adopt/repair-source.

## Fuera de alcance

Alcance avanzado de music search no aprobado; escrituras de catálogo no autorizadas; LLM.

## Reglas de negocio demostrables

- Audio vía proveedores aprobados + demos.
- No afirmar streaming comercial licenciado.

## Casos de uso recuperables

1. Buscar local → YouTube → adopt.
2. Reproducir track con resolver.
3. Repair-source cuando aplique.

## Criterios de aceptación verificables

- Núcleo music-search implementado (STATUS).
- fbf31a33 music-core.
- Pendiente smoke con API key real.

## Incertidumbres explícitas

- Detalle FR original 033 no disponible; núcleo posterior puede exceder/subconjunto el original.
