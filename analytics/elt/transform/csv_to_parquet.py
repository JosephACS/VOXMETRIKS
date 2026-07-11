#!/usr/bin/env python3
"""
Convierte un CSV externo a Bronze Parquet (setup puntual).

Uso: python elt/transform/csv_to_parquet.py ruta/al/archivo.csv

No uses data/raw/ — sube el CSV a PocketBase o pásalo como argumento.
Para ELT completo: python scripts/import_from_pocketbase.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BRONZE_DIR = ROOT / "data" / "bronze"
BRONZE_PARQUET = BRONZE_DIR / "raw_spotify.parquet"


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python elt/transform/csv_to_parquet.py <archivo.csv>")
        print("Recomendado: subir CSV a PocketBase y correr import_from_pocketbase.py")
        return 1

    csv_path = Path(sys.argv[1])
    if not csv_path.is_file():
        print(f"No existe: {csv_path}")
        return 1

    print(f"Leyendo {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Registros: {len(df):,}")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(BRONZE_PARQUET, index=False)
    print(f"Bronze: {BRONZE_PARQUET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
