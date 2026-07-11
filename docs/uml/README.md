# UML — Voxmetriks

Diagramas PlantUML derivados de specs **001–013**, `TRACEABILITY-MASTER.md` y código verificado.

## Estructura

| Carpeta | Contenido |
|---------|-----------|
| [use-cases/](use-cases/) | Casos de uso agregados y por paquete (`packages/uc-*.puml`) |
| [components/](components/) | Componentes frontend/backend |
| [architecture/](architecture/) | Arquitectura de despliegue y Medallion |
| [elt/](elt/) | Flujo ELT (CLI vs consola UI) |
| [classes/](classes/) | Modelo de clases core y warehouse |
| [sequence/](sequence/) | Secuencias login, play, recomendaciones |
| [context/](context/) | Vista de paquetes / contexto |
| [_rendered/](_rendered/) | PNG exportados (subcarpetas por tipo) |

## Renderizar

### PlantUML CLI

```bash
java -jar plantuml.jar docs/uml/**/*.puml

# Docker
docker run --rm -v "%cd%/docs/uml:/data" plantuml/plantuml /data/**/*.puml
```

### VS Code / Cursor

Extensión **PlantUML** → preview → export PNG/SVG.

## Trazabilidad

- Matriz de casos de uso: `automation/specs/TRACEABILITY-MASTER.md`
- Pipeline UI vs CLI: `automation/specs/008-pipeline-monitoring/spec.md`
- Implementación: `elt/pipelines/elt_pipeline.py`
