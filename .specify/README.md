# Spec Kit — VOXMETRIKS

Gobernanza Spec-Driven Development (SDD) del repositorio.  
**Verdad de producto (runtime):** [`docs/STATUS.md`](../docs/STATUS.md)  
**Principios:** [`.specify/memory/constitution.md`](memory/constitution.md)

## Piezas y roles

| Artefacto | Rol |
|-----------|-----|
| **Constitution** | Principios (P0–P20). No es checklist de features. |
| **Spec** | Qué / por qué / aceptación. Una Spec puede contener **varios casos de uso cohesionados**. |
| **Plan** | Arquitectura e impacto técnico de una Spec activa. |
| **Tasks** | Paquetes de trabajo para Cursor/agentes. **Los paquetes de Cursor no son Specs.** |
| **Closure** | Evidencia de cierre, deudas aceptadas, commits. |

## Cuándo crear una Spec nueva

Solo cambios **estructurales** o features **no triviales** requieren Spec nueva bajo `.specify/features/`.  
Correcciones locales, copy, tests y docs menores **no** abren Spec automáticamente.

## Numeración

- Prefijo de **tres dígitos** obligatorio (`001`…`999`).
- **IDs históricos inmutables** — no renumerar, no reutilizar.
- **Spec activa:** ninguna. El siguiente ID disponible es `052`.

## Carpetas canónicas

| Ruta | Contenido |
|------|-----------|
| [`.specify/features/`](features/) | **Solo features activas** de implementación. Hoy: ninguna. |
| [`.specify/history/`](history/) | Specs **cerradas** o **reconstruidas** (001–051). |
| [`.specify/CAPABILITY_MAP.md`](CAPABILITY_MAP.md) | Mapa de familias → Specs/packages → STATUS (sin duplicar runtime). |
| [`.specify/feature.json`](feature.json) | Puntero de compatibilidad Spec Kit (idle/closed). |

**MUST NOT** recrear almacenes de specs en la raíz (`specs/`) ni bajo `automation/specs/` como canónicos.

## Flujo

Constitution → Specify → [Clarify] → [Checklist] → Plan → Tasks → [Analyze] → Implement → Closure → mover a `history/`.
