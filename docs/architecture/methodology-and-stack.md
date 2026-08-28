# Cómo se construyó Voxmetriks

## 1. Qué significa Spec-Driven Development

Spec-Driven Development (SDD) significa que la especificación es el punto de partida y la referencia del trabajo. Antes de cambiar una parte importante, se deja claro qué problema se resuelve, qué debe ocurrir, qué queda fuera y cómo se va a comprobar.

En Voxmetriks se usa GitHub Spec Kit con esta cadena:

`Constitution → Specify → Clarify → Checklist → Plan → Tasks → Analyze → Implement → Validate → Evidence → Close`

No es burocracia por sí misma. Es una forma de evitar que una idea termine convertida en una pantalla bonita que no cumple el flujo real.

## 2. Cómo se aplicó en este proyecto

1. **Constitution:** se fijaron las reglas del producto y de la arquitectura en `.specify/memory/constitution.md`.
2. **Specify:** cada feature no trivial se describió en `.specify/features/` con requisitos y criterios de aceptación.
3. **Clarify y checklist:** se resolvieron dudas, límites, permisos, datos sintéticos y casos de error antes de programar.
4. **Plan y tasks:** se dividió el trabajo en cambios pequeños y verificables.
5. **Implement:** se modificaron Angular, FastAPI, DuckDB y el pipeline ELT sin reescribir el producto desde cero.
6. **Validate:** se combinaron pruebas automáticas, lint, build, comprobaciones del backend y revisión visual en dark y light.
7. **Evidence y close:** se conservaron resultados, documentación, diagramas, datos de demo y commits para poder explicar qué quedó implementado.

## 3. Qué herramientas se usaron

| Capa | Herramienta | Para qué sirve |
| --- | --- | --- |
| Interfaz | Angular + TypeScript | Pantallas, rutas, menú, temas y reproductor. |
| Componentes | Angular Material/CDK + CSS tokens | Controles, accesibilidad y design system ámbar. |
| Backend | Python + FastAPI + Pydantic | API, reglas, permisos y validación de datos. |
| Datos | DuckDB | Warehouse local de demo: catálogo, operación y analítica. |
| Ingesta | ELT Bronze → Silver → Gold, Parquet y Airflow local | Preparar y actualizar el catálogo de forma trazable. |
| Audio | Spotify Web Playback SDK + Deezer API | Spotify completo con sesión; Deezer como preview de respaldo. |
| Seguridad | Sesiones, RBAC y contexto de organización | Separar usuarios, espacios y permisos. |
| Calidad | Vitest, pytest, ESLint y Ruff | Detectar regresiones y mantener el código consistente. |
| Verificación | Navegador local y revisión visual | Comprobar que la experiencia realmente se entiende. |
| Versionado | Git + GitHub | Historial, commits y entrega reproducible en otra laptop. |

## 4. Respuesta corta para explicarlo

> “Primero describí el comportamiento en una spec; después hice el plan y las tareas, lo implementé por partes y lo validé con pruebas y revisión visual. Angular muestra la experiencia, FastAPI aplica las reglas, DuckDB guarda el catálogo y la analítica, y Spotify/Deezer resuelven el audio. Cada cierre queda respaldado por evidencia y por un commit.”

## 5. Límites que conviene decir con honestidad

- Los datos empresariales de la cuenta demo son sintéticos y están preparados para enseñar el flujo.
- DuckDB es el warehouse de esta demo local; no se presenta como una base OLTP de producción multiusuario.
- Deezer entrega previews de 30 segundos y la interfaz lo informa.
- Spotify requiere una sesión conectada para playback completo.
- No se afirma que Voxmetriks sea un servicio comercial de streaming ni que procese dinero real.
