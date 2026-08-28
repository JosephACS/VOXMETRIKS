#!/usr/bin/env python3
"""
Spec 048 — Orchestrated Medallion stages for Apache Airflow.

Coordinates the canonical ELT in analytics/elt/pipelines/elt_pipeline.py.
Does NOT duplicate transforms. Stages communicate via Parquet/DuckDB on disk,
never via DataFrames in XCom.

CLI:
  python analytics/elt/pipelines/orchestrated_pipeline.py <stage> [--dag-run-id ID]

Stages:
  preflight | extract_bronze | transform_silver | load_staging
  | build_gold_and_aggregates | export_gold | validate_warehouse | finalize_run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project imports resolve when invoked via Airflow subprocess.
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[3]
_ANALYTICS = _PROJECT_ROOT / "analytics"
for _p in (str(_PROJECT_ROOT), str(_ANALYTICS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Prefer package imports (same as backend); fall back to file load for isolated CLI.
try:
    from elt.pipelines import elt_pipeline as elt  # type: ignore
    from elt.transform.enterprise_analytics import (  # type: ignore
        apply_enterprise_schema,
        register_pipeline_stage,
    )
except ImportError:
    elt = _load_module("elt_pipeline_orch", _THIS.parent / "elt_pipeline.py")
    _ent = _load_module(
        "enterprise_analytics_orch",
        _THIS.parents[1] / "transform" / "enterprise_analytics.py",
    )
    apply_enterprise_schema = _ent.apply_enterprise_schema
    register_pipeline_stage = _ent.register_pipeline_stage

logger = logging.getLogger("voxmetriks.orchestrated")

# Exact ctl stages that must be OK before finalize_run may succeed.
REQUIRED_STAGES_BEFORE_FINALIZE = (
    "extract_bronze",
    "transform_silver",
    "load_staging",
    "build_gold_and_aggregates",
    "export_gold",
    "validate_warehouse",
)


def dag_run_id_to_ctl_run_id(dag_run_id: str) -> int:
    """Deterministic positive INTEGER for ctl_pipeline_stages.run_id (DuckDB INTEGER)."""
    digest = hashlib.sha256(dag_run_id.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16) % (2**31 - 1)
    return value if value > 0 else 1


def _emit(payload: Dict[str, Any]) -> None:
    """Print small JSON metadata only (safe for optional XCom; never DataFrames)."""
    print(json.dumps(payload, default=str), flush=True)


def _lock_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "conflicting lock",
            "could not set lock",
            "lock on file",
            "database is locked",
            "file is already open",
        )
    )


def _open_writable():
    try:
        return elt._open_connection(elt.DB_PATH, recreate=False)
    except Exception as exc:
        if _lock_error(exc):
            raise RuntimeError(
                "DuckDB warehouse is locked by another process. "
                "Stop the application runtime (start.ps1 / `make down`) "
                "before triggering the Airflow DAG. "
                f"Path={elt.DB_PATH}"
            ) from exc
        raise


def _require_bronze() -> Path:
    path = elt.BRONZE_PARQUET
    if not path.exists():
        raise RuntimeError(
            f"Bronze parquet missing: {path}. "
            "Run extract_bronze first or provide PocketBase credentials / cache."
        )
    return path


def _require_silver() -> Path:
    path = elt.SILVER_PARQUET
    if not path.exists():
        raise RuntimeError(
            f"Silver parquet missing: {path}. Run transform_silver first."
        )
    return path


def stage_preflight(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    logger.info("STAGE preflight dag_run_id=%s ctl_run_id=%s", dag_run_id, ctl_run_id)
    data_root = Path(os.environ.get("VOXMETRIKS_DATA_DIR", "").strip() or elt._DATA_ROOT)
    db_path = elt.DB_PATH
    issues: list[str] = []

    for label, path in (
        ("data_root", data_root),
        ("bronze_dir", elt.BRONZE_DIR),
        ("silver_dir", elt.SILVER_DIR),
        ("gold_dir", elt.GOLD_DIR),
        ("warehouse_dir", db_path.parent),
    ):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            issues.append(f"Cannot create {label}={path}: {exc}")

    has_bronze = elt.BRONZE_PARQUET.exists()
    has_pb = bool(elt.POCKETBASE_EMAIL and elt.POCKETBASE_PASSWORD)
    if not has_bronze and not has_pb:
        issues.append(
            "No Bronze cache and no PocketBase credentials "
            "(set POCKETBASE_EMAIL/POCKETBASE_PASSWORD or provide data/bronze/raw_spotify.parquet)."
        )

    # Probe DuckDB access (read then short write transaction) without mutating schema.
    try:
        conn = _open_writable()
        try:
            conn.execute("SELECT 1").fetchone()
            conn.execute("BEGIN")
            conn.execute("SELECT 1")
            conn.execute("ROLLBACK")
        finally:
            conn.close()
    except RuntimeError:
        raise
    except Exception as exc:
        if _lock_error(exc):
            raise RuntimeError(
                "DuckDB warehouse is locked by another process. "
                "Stop start.ps1 / application compose before running Airflow. "
                f"Path={db_path}"
            ) from exc
        issues.append(f"Cannot open DuckDB at {db_path}: {exc}")

    if issues:
        raise RuntimeError("preflight failed: " + " | ".join(issues))

    return {
        "stage": "preflight",
        "status": "OK",
        "dag_run_id": dag_run_id,
        "ctl_run_id": ctl_run_id,
        "db_path": str(db_path),
        "bronze_ready": has_bronze,
        "pocketbase_configured": has_pb,
    }


def stage_extract_bronze(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    t0 = time.time()
    pb = None
    if elt.POCKETBASE_EMAIL and elt.POCKETBASE_PASSWORD:
        pb = elt.PocketBaseClient(elt.POCKETBASE_URL, elt.POCKETBASE_EMAIL, elt.POCKETBASE_PASSWORD)
        if not pb.authenticate():
            logger.warning("PocketBase auth failed — will try cached bronze only")
            pb = None
    df = elt.bronze_extract(pb)
    ms = int((time.time() - t0) * 1000)
    if not elt.BRONZE_PARQUET.exists():
        elt.BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(elt.BRONZE_PARQUET, index=False)
    _record_stage(ctl_run_id, dag_run_id, "extract_bronze", "Bronze", ms, 0, len(df))
    return {
        "stage": "extract_bronze",
        "status": "OK",
        "rows": len(df),
        "bronze_path": str(elt.BRONZE_PARQUET),
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_transform_silver(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    bronze_path = _require_bronze()
    t0 = time.time()
    df_bronze = elt._bronze_from_parquet(bronze_path)
    if df_bronze is None or df_bronze.empty:
        raise RuntimeError(f"Bronze parquet empty or unreadable: {bronze_path}")
    df_silver = elt.silver_transform(df_bronze)
    if df_silver is None or df_silver.empty:
        raise RuntimeError("silver_transform produced an empty DataFrame")
    ms = int((time.time() - t0) * 1000)
    _record_stage(
        ctl_run_id, dag_run_id, "transform_silver", "Silver", ms, len(df_bronze), len(df_silver)
    )
    return {
        "stage": "transform_silver",
        "status": "OK",
        "rows": len(df_silver),
        "silver_path": str(elt.SILVER_PARQUET),
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_load_staging(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    silver_path = _require_silver()
    import pandas as pd

    df = pd.read_parquet(silver_path)
    if df.empty:
        raise RuntimeError(f"Silver parquet is empty: {silver_path}")

    conn = _open_writable()
    t0 = time.time()
    rows = 0
    # Idempotent DDL outside the data transaction (DuckDB DDL may auto-commit).
    elt.apply_schema(conn)
    apply_enterprise_schema(conn)
    try:
        conn.execute("BEGIN TRANSACTION")
        rows = elt.gold_load_staging(conn, df)
        ms = int((time.time() - t0) * 1000)
        _record_stage_on_conn(
            conn, ctl_run_id, dag_run_id, "load_staging", "Gold", ms, len(df), rows
        )
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception as rb_exc:
            logger.error("ROLLBACK failed after load_staging error: %s", rb_exc)
        raise
    finally:
        conn.close()

    return {
        "stage": "load_staging",
        "status": "OK",
        "rows": rows,
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_build_gold_and_aggregates(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    conn = _open_writable()
    t0 = time.time()
    fact_rows = 0
    elt.apply_schema(conn)
    apply_enterprise_schema(conn)
    try:
        conn.execute("BEGIN TRANSACTION")
        elt.gold_build_warehouse(conn)
        fact_rows = int(conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0])
        ms = int((time.time() - t0) * 1000)
        _record_stage_on_conn(
            conn,
            ctl_run_id,
            dag_run_id,
            "build_gold_and_aggregates",
            "Gold",
            ms,
            0,
            fact_rows,
        )
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception as rb_exc:
            logger.error("ROLLBACK failed after build_gold error: %s", rb_exc)
        raise
    finally:
        conn.close()

    return {
        "stage": "build_gold_and_aggregates",
        "status": "OK",
        "fact_rows": fact_rows,
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_export_gold(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    conn = _open_writable()
    t0 = time.time()
    exported = 0
    try:
        # Strict for orchestrated / Airflow path — never OK with partial/zero exports.
        exported = elt._export_gold_parquets(conn, strict=True)
        if exported <= 0:
            raise RuntimeError("export_gold produced zero Parquet files")
        ms = int((time.time() - t0) * 1000)
        _record_stage_on_conn(
            conn,
            ctl_run_id,
            dag_run_id,
            "export_gold",
            "Gold",
            ms,
            0,
            exported,
            details=f"dag_run_id={dag_run_id}; exported={exported}",
        )
        conn.commit()
    except Exception:
        # Do not record export_gold=OK on failure / partial export.
        raise
    finally:
        conn.close()
    return {
        "stage": "export_gold",
        "status": "OK",
        "exported": exported,
        "gold_dir": str(elt.GOLD_DIR),
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_validate_warehouse(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    conn = _open_writable()
    t0 = time.time()
    ok = False
    try:
        ok = elt.verify_warehouse(conn)
        ms = int((time.time() - t0) * 1000)
        _record_stage_on_conn(
            conn,
            ctl_run_id,
            dag_run_id,
            "validate_warehouse",
            "Gold",
            ms,
            0,
            0,
            status="OK" if ok else "ERROR",
            details=f"dag_run_id={dag_run_id}; verify={ok}",
        )
        conn.commit()
    finally:
        conn.close()
    if not ok:
        raise SystemExit(2)
    return {
        "stage": "validate_warehouse",
        "status": "OK",
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def stage_finalize_run(*, dag_run_id: str, ctl_run_id: int) -> Dict[str, Any]:
    """Register success only when the exact required stage set completed OK."""
    conn = _open_writable()
    try:
        apply_enterprise_schema(conn)
        rows = conn.execute(
            """
            SELECT stage, status FROM ctl_pipeline_stages
            WHERE run_id = ?
            """,
            [ctl_run_id],
        ).fetchall()
        by_stage: Dict[str, str] = {}
        for stage_name, status in rows:
            # Keep worst status if duplicated.
            prev = by_stage.get(stage_name)
            if prev == "ERROR" or status == "ERROR":
                by_stage[stage_name] = "ERROR"
            else:
                by_stage[stage_name] = status

        # Validations first — even after a prior finalize_run=OK.
        errors = [s for s, st in by_stage.items() if st != "OK"]
        if errors:
            raise RuntimeError(
                f"Cannot finalize run ctl_run_id={ctl_run_id}: non-OK stages={errors}"
            )

        allowed_before_finalize = set(REQUIRED_STAGES_BEFORE_FINALIZE)
        unknown_ok = sorted(
            s for s in by_stage if s not in allowed_before_finalize and s != "finalize_run"
        )
        if unknown_ok:
            raise RuntimeError(
                f"Cannot finalize run ctl_run_id={ctl_run_id}: "
                f"unknown OK stages contaminate the run={unknown_ok}"
            )

        missing = [s for s in REQUIRED_STAGES_BEFORE_FINALIZE if by_stage.get(s) != "OK"]
        if missing:
            raise RuntimeError(
                f"Cannot finalize incomplete run ctl_run_id={ctl_run_id}: "
                f"missing required OK stages={missing}"
            )
        if by_stage.get("validate_warehouse") != "OK":
            raise RuntimeError(
                f"Cannot finalize without validate_warehouse OK (ctl_run_id={ctl_run_id})"
            )

        # Idempotent success only after the run still validates cleanly.
        if by_stage.get("finalize_run") == "OK":
            return {
                "stage": "finalize_run",
                "status": "OK",
                "already_finalized": True,
                "ctl_run_id": ctl_run_id,
                "dag_run_id": dag_run_id,
            }

        try:
            raw_count = int(conn.execute("SELECT COUNT(*) FROM raw_spotify").fetchone()[0])
        except Exception as count_exc:
            raise RuntimeError(
                f"Cannot finalize: unable to count raw_spotify: {count_exc}"
            ) from count_exc

        try:
            conn.execute("BEGIN TRANSACTION")
            elt._register_load(conn, "FULL", raw_count, raw_count, "EXITOSO")
            elt._audit(
                conn,
                "ELT_PIPELINE",
                "all",
                f"OK orchestrated dag_run_id={dag_run_id} ctl_run_id={ctl_run_id} rows={raw_count}",
            )
            _record_stage_on_conn(
                conn,
                ctl_run_id,
                dag_run_id,
                "finalize_run",
                "Control",
                0,
                raw_count,
                raw_count,
                details=f"dag_run_id={dag_run_id}",
            )
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception as rb_exc:
                logger.error("ROLLBACK failed after finalize_run error: %s", rb_exc)
            raise
    finally:
        conn.close()
    return {
        "stage": "finalize_run",
        "status": "OK",
        "already_finalized": False,
        "ctl_run_id": ctl_run_id,
        "dag_run_id": dag_run_id,
    }


def _record_stage(
    ctl_run_id: int,
    dag_run_id: str,
    stage: str,
    layer: str,
    duration_ms: int,
    rows_in: int,
    rows_out: int,
    status: str = "OK",
    details: str = "",
) -> None:
    conn = _open_writable()
    try:
        apply_enterprise_schema(conn)
        _record_stage_on_conn(
            conn, ctl_run_id, dag_run_id, stage, layer, duration_ms, rows_in, rows_out, status, details
        )
        conn.commit()
    finally:
        conn.close()


def _record_stage_on_conn(
    conn,
    ctl_run_id: int,
    dag_run_id: str,
    stage: str,
    layer: str,
    duration_ms: int,
    rows_in: int,
    rows_out: int,
    status: str = "OK",
    details: str = "",
) -> None:
    detail = details or f"dag_run_id={dag_run_id}"
    if "dag_run_id=" not in detail:
        detail = f"{detail}; dag_run_id={dag_run_id}"
    register_pipeline_stage(
        conn,
        ctl_run_id,
        stage,
        layer,
        duration_ms,
        rows_in,
        rows_out,
        status=status,
        details=detail[:500],
    )


STAGES = {
    "preflight": stage_preflight,
    "extract_bronze": stage_extract_bronze,
    "transform_silver": stage_transform_silver,
    "load_staging": stage_load_staging,
    "build_gold_and_aggregates": stage_build_gold_and_aggregates,
    "export_gold": stage_export_gold,
    "validate_warehouse": stage_validate_warehouse,
    "finalize_run": stage_finalize_run,
}


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
        stream=sys.stdout,
    )
    parser = argparse.ArgumentParser(description="VOXMETRIKS orchestrated ELT stage runner")
    parser.add_argument("stage", choices=sorted(STAGES.keys()))
    parser.add_argument(
        "--dag-run-id",
        default=os.environ.get("AIRFLOW_CTX_DAG_RUN_ID")
        or os.environ.get("VOXMETRIKS_DAG_RUN_ID")
        or f"manual-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        help="Airflow dag_run identifier (stored in ctl details)",
    )
    parser.add_argument(
        "--ctl-run-id",
        type=int,
        default=None,
        help="Override ctl_pipeline_stages.run_id (default: deterministic hash of dag-run-id)",
    )
    args = parser.parse_args(argv)
    ctl_run_id = args.ctl_run_id or dag_run_id_to_ctl_run_id(args.dag_run_id)
    logger.info(
        "Running stage=%s dag_run_id=%s ctl_run_id=%s DB_PATH=%s",
        args.stage,
        args.dag_run_id,
        ctl_run_id,
        elt.DB_PATH,
    )
    try:
        result = STAGES[args.stage](dag_run_id=args.dag_run_id, ctl_run_id=ctl_run_id)
        _emit(result)
        return 0
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
        _emit({"stage": args.stage, "status": "ERROR", "exit_code": code})
        return code if code else 1
    except Exception as exc:
        logger.error("Stage %s failed: %s", args.stage, exc, exc_info=True)
        _emit({"stage": args.stage, "status": "ERROR", "error": str(exc)[:500]})
        return 1


if __name__ == "__main__":
    sys.exit(main())
