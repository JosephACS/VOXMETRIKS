# Scripts operativos

Utilidades de desarrollo, datos y verificación. Ejecutar desde la **raíz del repo**.

## Estructura

```
scripts/
├── dev/          # Utilidades opcionales (árbol, PlantUML)
├── archive/      # Migraciones one-shot ya aplicadas
└── *.py          # Scripts activos (tabla abajo)
```

## Datos / warehouse

| Script | Uso |
|--------|-----|
| `import_from_pocketbase.py` | Importa dataset Spotify vía PocketBase → ELT |
| `upload_dataset_to_pocketbase.py` | Sube CSV a PocketBase (setup inicial; ruta como argumento) |
| `generate_activity.py` | Eventos sintéticos sobre catálogo real |
| `clean_track_names.py` | Limpia nombres sucios sin rebuild |
| `resolve_audio_youtube.py` | Pre-resuelve audio YouTube |
| `validate_warehouse.py` | Validación post-ELT |
| `analyze_warehouse.py` | Reporte calidad del warehouse |

## Smoke tests

Con el backend en marcha:

```bash
python scripts/smoke_api.py --base-url http://localhost:8000
python scripts/smoke_user_journey.py --base-url http://localhost:8000
```

## Desarrollo

| Script | Uso |
|--------|-----|
| `dev_start.bat` | Arranque local Windows (venv + ELT + API) |
| `install-git-hooks.sh` | Hook anti co-autores agente en commits |
| `install-ide-extensions.ps1` | Extensiones recomendadas VS Code/Cursor |
| `dev/print_tree.py` | Árbol de directorios |
| `dev/render_puml_png.py` | Render PlantUML → PNG |

## ELT desde Makefile

```bash
make etl        # backend/app/etl (boot builders)
make pipeline   # elt/pipelines/elt_pipeline.py (completo)
```

Material académico histórico retirado del working tree: ver [`docs/archive/README.md`](../../docs/archive/README.md) (`git show d2f6a27f:<path>`).
