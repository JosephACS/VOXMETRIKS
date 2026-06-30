# Scripts operativos

Utilidades de desarrollo, datos y verificación. Ejecutar desde la raíz del repo salvo que el script indique otra cosa.

## Desarrollo

| Script | Uso |
|--------|-----|
| `print_tree.py` | Imprime árbol de directorios (`python scripts/print_tree.py [ruta]`) |
| `dev_start.bat` | Arranque local en Windows (venv + ELT si falta DB + API) |
| `install-git-hooks.sh` | Instala hook que bloquea co-autores de agentes en commits |

## Datos / warehouse

| Script | Uso |
|--------|-----|
| `import_from_pocketbase.py` | Importa dataset Spotify real vía PocketBase → ELT |
| `generate_activity.py` | Genera eventos sintéticos sobre el catálogo real (no crea tracks falsos) |
| `upload_dataset_to_pocketbase.py` | Sube CSV a PocketBase (setup inicial) |
| `clean_track_names.py` | Limpia nombres sucios (` · #id`, `[syn-N]`, caracteres rotos) sin rebuild |
| `resolve_audio_youtube.py` | Pre-resuelve audio YouTube (API + fallback yt-dlp sin cuota diaria) |
| `validate_warehouse.py` | Validación rápida post-ELT |
| `analyze_warehouse.py` | Reporte de calidad y estadísticas del warehouse |

## Smoke tests (API real)

Con el backend en marcha:

```bash
python scripts/smoke_api.py --base-url http://localhost:8000
python scripts/smoke_user_journey.py --base-url http://localhost:8000
```

El rebuild completo del warehouse (`rebuild_warehouse_700k.py`) y los scripts académicos/legacy (TGA07, VOXMETRIK_V2) viven en [`../voxmetriks-entregas`](../voxmetriks-entregas).
