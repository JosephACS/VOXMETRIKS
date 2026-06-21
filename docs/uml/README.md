# UML — Voxmetriks (entregable bloque 3)

Diagramas PlantUML derivados de specs operativas **001–011**, `TRACEABILITY-MASTER.md` v2.0.0 y código verificado.

| Archivo | Contenido |
|---------|-----------|
| `01-use-cases.puml` | Casos de uso por spec / paquete (CU agregados) |
| `02-components.puml` | Componentes **compacto** FE/BE PKG-01..07 (PNG sin recorte) |
| `02-components-detailed.puml` | Mismo diagrama con cada componente interno (puede ser muy ancho) |
| `03-architecture.puml` | Arquitectura **compatible web** Docker + Medallion + SPA + API |
| `03-architecture-detailed.puml` | Variante con nodos anidados (puede dar error en plantuml.com) |
| `04-elt-flow.puml` | Flujo ELT real (CLI) vs consola UI (simulación + synthetic) |

## Renderizar

### Opción A — PlantUML CLI

```bash
# Instalar Java + plantuml (o usar Docker)
java -jar plantuml.jar docs/uml/*.puml

# Docker
docker run --rm -v "%cd%/docs/uml:/data" plantuml/plantuml /data/*.puml
```

Genera PNG/SVG junto a cada `.puml`.

### Opción B — VS Code / Cursor

Extensión **PlantUML** → `Alt+D` preview → export PNG/SVG.

### Opción C — Online (solo preview)

Copiar contenido a [https://www.plantuml.com/plantuml](https://www.plantuml.com/plantuml) (no subir secretos).

## Trazabilidad

- Casos de uso ↔ matriz: `specs/TRACEABILITY-MASTER.md`
- Delimitación ELT UI vs CLI: `specs/008-pipeline-monitoring/spec.md` §RB-PM01, FR-PM11–PM12, FR-PM24
- Arquitectura Medallion: `elt/pipelines/elt_pipeline.py`, Constitución §3–§4
- Despliegue: `docker-compose.yml` (pipeline → api, healthcheck `/health`)
