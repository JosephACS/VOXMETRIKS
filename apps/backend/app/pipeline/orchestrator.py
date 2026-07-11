from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.cache import cache_invalidate
from app.core.config import get_settings
from app.core.database import close_read_pool
from app.core.logging import get_logger
from app.db.duckdb_client import shutdown_duckdb_client
from app.db.init_db import ensure_data_directories
from app.etl.pipelines import run_full_etl
from app.utils.data_validation import validate_warehouse

logger = get_logger("voxmetrik.boot")

_BOOT_STATE: dict[str, Any] = {
    "completed": False,
    "started_at": None,
    "finished_at": None,
    "etl_status": "pending",
    "gold_ready": False,
    "validation": {},
}


def get_boot_state() -> dict[str, Any]:
    return dict(_BOOT_STATE)


def _etl_mode() -> str:
    return os.getenv("RUN_ETL_ON_BOOT", "auto").strip().lower()


def _release_connections() -> None:
    shutdown_duckdb_client()
    close_read_pool()
    get_settings.cache_clear()


def _try_legacy_elt(project_root: Path) -> bool:
    script = project_root / "elt" / "pipelines" / "elt_pipeline.py"
    if not script.exists():
        return False
    logger.info("[BOOT] Warehouse missing — running legacy ELT bootstrap...")
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", f"{project_root}{os.pathsep}{project_root / 'backend'}")
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
        if result.returncode != 0:
            logger.error("[BOOT] Legacy ELT failed code=%s stderr=%s", result.returncode, result.stderr[-500:])
            return False
        logger.info("[BOOT] Legacy ELT completed")
        return True
    except Exception as exc:
        logger.error("[BOOT] Legacy ELT error: %s", exc)
        return False


def _table_exists_name(table: str) -> bool:
    try:
        from app.db.duckdb_client import get_duckdb_client

        return table.lower() in {t.lower() for t in get_duckdb_client().list_tables()}
    except Exception:
        return False


def _warm_cache() -> None:
    logger.info("[CACHE] Warming dashboard cache...")
    cache_invalidate()
    try:
        from app.services.dashboard_service import DashboardService

        svc = DashboardService()
        svc.get_overview()
        svc.get_growth()
        svc.get_engagement()
        svc.get_realtime()
        logger.info("[CACHE] Dashboard cache warmed")
    except Exception as exc:
        logger.warning("[CACHE] Warm skipped: %s", exc)


def run_system_boot() -> dict[str, Any]:
    """Full system boot: init → ETL → GOLD → cache → validate."""
    global _BOOT_STATE
    boot_started = time.perf_counter()
    started = datetime.now(timezone.utc)
    _BOOT_STATE["started_at"] = started.isoformat()
    settings = get_settings()
    project_root = settings.data_root.parent

    logger.info("[BOOT] Initializing VOXMETRIK_V2...")
    ensure_data_directories()
    db_path = settings.db_path_resolved
    logger.info("[BOOT] Connecting DuckDB path=%s", db_path)

    _release_connections()

    if not db_path.exists():
        _try_legacy_elt(project_root)

    mode = _etl_mode()
    validation = validate_warehouse() if db_path.exists() else None
    run_etl = mode not in ("never", "false", "0", "off") and (
        mode == "always" or (mode == "auto" and (validation is None or not validation.gold_ready))
    )

    etl_result: dict[str, Any] = {"status": "skipped"}
    if run_etl and db_path.exists():
        if _table_exists_name("raw_spotify"):
            logger.info("[ETL] Running bronze pipeline...")
            logger.info("[ETL] Running silver pipeline...")
            logger.info("[GOLD] Building analytics...")
            _release_connections()
            try:
                etl_result = run_full_etl()
                _BOOT_STATE["etl_status"] = etl_result.get("status", "error")
            except Exception as exc:
                logger.exception("[ETL] V2 pipeline failed")
                etl_result = {"status": "error", "errors": [str(exc)]}
                _BOOT_STATE["etl_status"] = "error"
        elif not validation or not validation.tables_ok:
            if _try_legacy_elt(project_root):
                _release_connections()
                if _table_exists_name("raw_spotify"):
                    etl_result = run_full_etl()
                    _BOOT_STATE["etl_status"] = etl_result.get("status", "error")
                else:
                    _BOOT_STATE["etl_status"] = "legacy_only"
            else:
                _BOOT_STATE["etl_status"] = "no_source"
        else:
            logger.info("[ETL] Skipped — warehouse present, gold may need manual refresh")
            _BOOT_STATE["etl_status"] = "skipped"
    elif not db_path.exists():
        _BOOT_STATE["etl_status"] = "no_warehouse"
    else:
        _BOOT_STATE["etl_status"] = "skipped"

    _release_connections()
    _warm_cache()

    final_validation = validate_warehouse() if db_path.exists() else None
    _BOOT_STATE["gold_ready"] = bool(final_validation and final_validation.gold_ready)
    _BOOT_STATE["validation"] = {
        "tables_ok": final_validation.tables_ok if final_validation else False,
        "gold_ready": _BOOT_STATE["gold_ready"],
        "row_counts": final_validation.row_counts if final_validation else {},
        "errors": final_validation.errors if final_validation else ["no_warehouse"],
    }
    _BOOT_STATE["completed"] = True
    _BOOT_STATE["finished_at"] = datetime.now(timezone.utc).isoformat()
    _BOOT_STATE["elapsed_ms"] = round((time.perf_counter() - boot_started) * 1000, 2)

    _release_connections()
    logger.info("[SUCCESS] System ready on port %s", settings.port)
    return get_boot_state()
