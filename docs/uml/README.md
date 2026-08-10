# UML — fuentes canónicas

Solo fuentes `.puml`. Los PNG se regeneran localmente (no versionar `_rendered/`).

## Diagrama

| Fuente | Tema |
|--------|------|
| `architecture/03-architecture-detailed.puml` | Arquitectura detallada |
| `components/02a-components-frontend.puml` | Componentes frontend |
| `components/02b-components-backend-datos.puml` | Componentes backend/datos |
| `context/10-packages.puml` | Contexto de paquetes |
| `elt/04-elt-flow.puml` | ELT |
| `classes/05-classes-core.puml` | Clases principales |
| `classes/06-classes-warehouse.puml` | Clases warehouse |
| `sequence/07-seq-login.puml` | Secuencia login |
| `sequence/08-seq-play.puml` | Secuencia play |
| `sequence/09-seq-recommendations.puml` | Secuencia recommendations |
| `sequence/11-strategic-decision-flow.puml` | Objetivo → KPI → decisión → acción |
| `deployment/12-deployment.puml` | Despliegue app + Airflow |
| `use-cases/01-use-cases.puml` | Caso de uso general |

## Regeneración

```bash
# Requiere plantuml en PATH
mkdir -p docs/uml/_rendered
plantuml -tpng -o ../_rendered docs/uml/architecture/*.puml
plantuml -tpng -o ../_rendered docs/uml/components/*.puml
plantuml -tpng -o ../_rendered docs/uml/context/*.puml
plantuml -tpng -o ../_rendered docs/uml/elt/*.puml
plantuml -tpng -o ../_rendered docs/uml/classes/*.puml
plantuml -tpng -o ../_rendered docs/uml/sequence/*.puml
plantuml -tpng -o ../_rendered docs/uml/use-cases/*.puml
plantuml -tpng -o ../_rendered docs/uml/deployment/*.puml
```

`docs/uml/_rendered/` está en `.gitignore`.
