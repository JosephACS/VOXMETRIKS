from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.duckdb_client import get_duckdb_client, shutdown_duckdb_client

logger = get_logger(__name__)

MEDALLION_DIRS = ("raw", "bronze", "silver", "gold", "warehouse")


def ensure_data_directories() -> None:
    """Create medallion data directories if missing."""
    settings = get_settings()
    root = settings.data_root
    for name in MEDALLION_DIRS:
        path = root / name
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("data_dir_ready path=%s", path)


def bootstrap_database() -> dict:
    """
    Validate warehouse availability and return bootstrap metadata.
    Does not mutate schema — ETL owns DDL.
    """
    ensure_data_directories()
    settings = get_settings()
    db_path: Path = settings.db_path_resolved

    if not db_path.exists():
        logger.warning("warehouse_missing path=%s", db_path)
        return {
            "ready": False,
            "path": str(db_path),
            "table_count": 0,
            "message": "Warehouse file not found. Run ELT pipeline first.",
        }

    client = get_duckdb_client()
    tables = client.list_tables()
    version = client.fetch_scalar("SELECT version()", label="bootstrap_version")
    logger.info("warehouse_ready path=%s tables=%s", db_path, len(tables))
    return {
        "ready": True,
        "path": str(db_path),
        "table_count": len(tables),
        "duckdb_version": version,
        "message": "Warehouse connected",
    }


def shutdown_database() -> None:
    shutdown_duckdb_client()
