#!/usr/bin/env python3
"""
Descarga el CSV desde PocketBase y lo convierte directo a Bronze Parquet.

No escribe CSV en data/raw/ — PocketBase es la fuente; Bronze es la cache local.

Preferir: python scripts/import_from_pocketbase.py (ELT completo).
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BRONZE_DIR = ROOT / "data" / "bronze"
BRONZE_PARQUET = BRONZE_DIR / "raw_spotify.parquet"

# URL del archivo en PocketBase (ajusta record/file si cambia)
FILE_URL = os.environ.get(
    "POCKETBASE_DATASET_URL",
    "http://127.0.0.1:8090/api/files/datasets/cc9arh0oe73ifc5/dataset_4unz6fyld6.csv",
)


def main() -> int:
    print("Descargando dataset desde PocketBase (sin CSV local)...")
    resp = httpx.get(FILE_URL, timeout=120, follow_redirects=True)
    if resp.status_code != 200:
        print(f"Error {resp.status_code} descargando desde PocketBase")
        return 1

    df = pd.read_csv(io.BytesIO(resp.content))
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(BRONZE_PARQUET, index=False)
    print(f"Bronze cache: {BRONZE_PARQUET} ({len(df):,} filas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
