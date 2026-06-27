#!/usr/bin/env python3
"""
Import the real Spotify catalog from PocketBase into DuckDB.

PocketBase is the authoritative source (~100k tracks). This script runs the
full ELT pipeline (Bronze → Silver → Gold). No synthetic bootstrap.

Requires:
  - PocketBase running at POCKETBASE_URL (default http://127.0.0.1:8090)
  - CSV uploaded to collection PB_COLLECTION (default: datasets)
  - POCKETBASE_EMAIL / POCKETBASE_PASSWORD in .env

After import, generate synthetic activity from the UI (/elt-pipeline) or:
    python scripts/generate_activity.py --target 1600000

Usage (repo root):
    python scripts/import_from_pocketbase.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"


def main() -> None:
    if WAREHOUSE.exists():
        backup = WAREHOUSE.with_suffix(".duckdb.bak")
        shutil.copy2(WAREHOUSE, backup)
        WAREHOUSE.unlink()
        print(f"[import] Backup -> {backup}")

    from elt.pipelines.elt_pipeline import run_pipeline

    print("[import] PocketBase -> DuckDB (full ELT, no synthetic bootstrap)...")
    result = run_pipeline()
    print(f"[import] OK — {result.get('rows_loaded', 0):,} rows ({result.get('source')})")
    print("[import] Restart the API if it is already running.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"[import] FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
