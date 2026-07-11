from __future__ import annotations

import os
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
from app.etl.canonical_adapter import invoke_canonical_elt, resolve_canonical_script
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
    "etl_mode": None,
}

# RUN_ETL_ON_BOOT modes (Spec 014 E)
#   never|false|0|off     — disabled (no ETL)
#   validate|validation   — validation-only (no transform)
#   always                — backend gold refresh when raw_spotify exists;
#                           canonical analytics/elt only if warehouse missing
#   auto|if_missing       — ETL when gold not ready / warehouse missing
#   full|rebuild          — explicit full canonical rebuild (ops only; long-running)
_DISABLED = frozenset({"never", "false", "0", "off"})
_VALIDATE_ONLY = frozenset({"validate", "validation", "validation-only", "validation_only"})
_FULL_REBUILD = frozenset({"full", "rebuild", "full_rebuild"})


def get_boot_state() -> dict[str, Any]:
    return dict(_BOOT_STATE)


def _etl_mode() -> str:
    return os.getenv("RUN_ETL_ON_BOOT", "auto").strip().lower()


def _release_connections() -> None:
    shutdown_duckdb_client()
    close_read_pool()
    get_settings.cache_clear()


def _try_canonical_elt(project_root: Path, *, db_path: Path | None = None) -> bool:
    """Bootstrap via canonical analytics/elt (missing warehouse / explicit full)."""
    script = resolve_canonical_script(project_root)
    if script is None:
        logger.warning("[BOOT] Canonical ELT script not found under %s", project_root)
        return False
    logger.info("[BOOT] Warehouse bootstrap — canonical ELT %s", script)
    outcome = invoke_canonical_elt(cwd=project_root, db_path=db_path)
    return outcome.get("status") == "ok"


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
        import duckdb

        from app.services.dashboard_service import DashboardService

        svc = DashboardService()
        svc.get_overview()
        svc.get_growth()
        svc.get_engagement()
        svc.get_realtime()
        logger.info("[CACHE] Dashboard cache warmed")
    except duckdb.Error as exc:
        logger.warning("[CACHE] Warm skipped (warehouse schema/query): %s", exc)
    except Exception:
        logger.exception("[CACHE] Warm failed with unexpected error")
        raise


def run_system_boot() -> dict[str, Any]:
    """System boot: init → optional ETL → cache warm → validate.

    Full analytics/elt rebuild is never the default when the warehouse already
    exists (would block API startup). Use ``make pipeline`` or
    ``RUN_ETL_ON_BOOT=full`` explicitly for ops rebuilds.
    """
    global _BOOT_STATE
    boot_started = time.perf_counter()
    started = datetime.now(timezone.utc)
    _BOOT_STATE["started_at"] = started.isoformat()
    settings = get_settings()
    project_root = settings.data_root.parent
    mode = _etl_mode()
    _BOOT_STATE["etl_mode"] = mode

    logger.info("[BOOT] Initializing VOXMETRIK_V2 mode=%s...", mode)
    ensure_data_directories()
    db_path = settings.db_path_resolved
    logger.info("[BOOT] Connecting DuckDB path=%s", db_path)

    _release_connections()

    if not db_path.exists() and mode not in _DISABLED | _VALIDATE_ONLY:
        _try_canonical_elt(project_root, db_path=db_path)
        _release_connections()

    validation = validate_warehouse() if db_path.exists() else None
    etl_result: dict[str, Any] = {"status": "skipped"}

    if mode in _DISABLED:
        _BOOT_STATE["etl_status"] = "skipped"
        logger.info("[ETL] Disabled (RUN_ETL_ON_BOOT=%s)", mode)
    elif mode in _VALIDATE_ONLY:
        _BOOT_STATE["etl_status"] = "validation_only"
        logger.info("[ETL] Validation-only mode — no transforms")
    elif mode in _FULL_REBUILD:
        logger.warning(
            "[ETL] Full rebuild requested — invoking canonical analytics/elt "
            "(may take a long time; prefer make pipeline outside API boot)"
        )
        _release_connections()
        ok = _try_canonical_elt(project_root, db_path=db_path)
        _BOOT_STATE["etl_status"] = "ok" if ok else "error"
        etl_result = {"status": _BOOT_STATE["etl_status"], "source": "canonical_analytics_elt"}
        _release_connections()
    else:
        # always | auto | if_missing
        run_backend_etl = mode == "always" or (
            mode in ("auto", "if_missing")
            and (validation is None or not validation.gold_ready)
        )
        if run_backend_etl and db_path.exists():
            if _table_exists_name("raw_spotify"):
                logger.info("[ETL] Backend runtime refresh (Bronze→Silver→Gold)...")
                _release_connections()
                try:
                    etl_result = run_full_etl()
                    _BOOT_STATE["etl_status"] = etl_result.get("status", "error")
                except Exception as exc:
                    logger.exception("[ETL] Backend runtime pipeline failed")
                    etl_result = {"status": "error", "errors": [str(exc)]}
                    _BOOT_STATE["etl_status"] = "error"
            elif not validation or not validation.tables_ok:
                if _try_canonical_elt(project_root, db_path=db_path):
                    _release_connections()
                    if _table_exists_name("raw_spotify"):
                        etl_result = run_full_etl()
                        _BOOT_STATE["etl_status"] = etl_result.get("status", "error")
                    else:
                        _BOOT_STATE["etl_status"] = "canonical_only"
                else:
                    _BOOT_STATE["etl_status"] = "no_source"
            else:
                logger.info("[ETL] Skipped — warehouse present; gold refresh not required")
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
    _BOOT_STATE["etl_result"] = {
        "status": etl_result.get("status"),
        "errors": etl_result.get("errors", []),
    }

    _release_connections()
    logger.info("[SUCCESS] System ready on port %s", settings.port)
    return get_boot_state()
