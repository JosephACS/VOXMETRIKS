"""Medallion layer paths for warehouse status."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BRONZE_PARQUET = PROJECT_ROOT / "data" / "bronze" / "raw_spotify.parquet"
SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "silver_spotify.parquet"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
