# Data — VOXMETRIK V2

Estructura Medallion. **No guardes CSV local**: el catálogo autoritativo está en **PocketBase** (nube).

```
data/
├── warehouse/          ← DuckDB canónico (voxmetrik.duckdb) — generado por ELT
├── bronze/             ← raw_spotify.parquet (cache post-sync PocketBase)
├── silver/             ← silver_spotify.parquet (limpieza / tipado)
└── gold/               ← exports Parquet opcionales para BI
```

## Flujo

1. **PocketBase** — dataset Spotify (~100k tracks) en colección `datasets`.
2. **ELT** — `python automation/scripts/import_from_pocketbase.py` o UI `/elt-pipeline`.
3. **Bronze** — escribe `bronze/raw_spotify.parquet` (sin CSV intermedio en disco).
4. **Silver → Gold** — `silver/silver_spotify.parquet` → `warehouse/voxmetrik.duckdb`.

## Setup inicial (una sola vez)

Sube el CSV **directo a PocketBase** (no a `data/`):

```bash
python automation/scripts/upload_dataset_to_pocketbase.py ruta/al/spotify_dataset.csv
```

## Git

Archivos generados (`*.duckdb`, `*.parquet`, `*.csv`) están en `.gitignore`.  
Solo se versionan `.gitkeep` y este README.
