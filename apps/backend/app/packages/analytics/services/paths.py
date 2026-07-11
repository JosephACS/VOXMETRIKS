"""Medallion layer paths for warehouse status."""

from pathlib import Path

from app.core.config import get_settings


def _project_root() -> Path:
    return get_settings().data_root.parent


PROJECT_ROOT = _project_root()
BRONZE_PARQUET = PROJECT_ROOT / "data" / "bronze" / "raw_spotify.parquet"
SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "silver_spotify.parquet"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
