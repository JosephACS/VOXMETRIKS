"""Analytical event inventory and classification helpers (read-only)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import duckdb

from app.core.database import table_exists
from app.core.query_helpers import count_rows
from app.core.response_cache import cached_response

from .constants import ACTIVITY_FACT_TABLES

logger = logging.getLogger(__name__)

VALID_CLASSIFICATIONS = frozenset({"real", "imported", "demo", "synthetic", "unknown"})


def _safe_count(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    if not table_exists(conn, table):
        return 0
    return count_rows(conn, table)


def _latest_activity_load(conn: duckdb.DuckDBPyConnection) -> Optional[Dict[str, Any]]:
    """Return the most recent ctl_carga_dataset row when the table exists."""
    if not table_exists(conn, "ctl_carga_dataset"):
        return None
    try:
        cols = {r[0] for r in conn.execute("DESCRIBE ctl_carga_dataset").fetchall()}
    except Exception:
        logger.exception("events_inventory: describe ctl_carga_dataset failed")
        return None

    order_col = "fecha_carga" if "fecha_carga" in cols else ("id_carga" if "id_carga" in cols else None)
    if not order_col:
        return None

    select_cols = [c for c in ("id_carga", "fecha_carga", "modo", "total_raw", "total_procesados", "estado") if c in cols]
    if not select_cols:
        return None
    try:
        row = conn.execute(
            f'SELECT {", ".join(select_cols)} FROM ctl_carga_dataset ORDER BY {order_col} DESC LIMIT 1'
        ).fetchone()
    except Exception:
        logger.exception("events_inventory: latest ctl_carga_dataset query failed")
        return None
    if not row:
        return None
    return dict(zip(select_cols, row))


def classify_activity_facts(conn: duckdb.DuckDBPyConnection) -> str:
    """
    Table-level classification for ACTIVITY_FACT_TABLES.

    No per-row provenance columns exist on fact_* activity tables.
    When the latest successful load mode is synthetic_activity_* we treat
    the current activity-fact corpus as synthetic; otherwise unknown.
    """
    load = _latest_activity_load(conn)
    if not load:
        return "unknown"
    modo = str(load.get("modo") or "").lower()
    estado = str(load.get("estado") or "").upper()
    if estado and estado not in {"OK", "EXITOSO", "SUCCESS"}:
        return "unknown"
    if modo.startswith("synthetic_activity") or "synthetic_activity" in modo:
        return "synthetic"
    if modo.startswith("synthetic_target") or modo.startswith("synthetic"):
        return "synthetic"
    return "unknown"


def _table_max_event_ts(conn: duckdb.DuckDBPyConnection, table: str) -> Optional[str]:
    if not table_exists(conn, table):
        return None
    try:
        cols = {r[0] for r in conn.execute(f'DESCRIBE "{table}"').fetchall()}
    except Exception:
        return None
    for candidate in ("fecha_evento", "session_end", "session_start", "updated_at", "created_at"):
        if candidate not in cols:
            continue
        try:
            row = conn.execute(f'SELECT MAX("{candidate}") FROM "{table}"').fetchone()
        except Exception:
            continue
        if row and row[0] is not None:
            val = row[0]
            if hasattr(val, "isoformat"):
                return val.isoformat()
            return str(val)
    return None


@cached_response(ttl_seconds=30.0, key="get_events_breakdown")
def get_events_breakdown(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """
    Transparent inventory for the Home “analytical events” KPI.

    total_events = sum(COUNT(*)) over ACTIVITY_FACT_TABLES (base tables only).
    Does not count dimensions, aggregates, app_*, views, or duplicate joins.
    """
    classification = classify_activity_facts(conn)
    if classification not in VALID_CLASSIFICATIONS:
        classification = "unknown"

    load = _latest_activity_load(conn)
    tables: List[Dict[str, Any]] = []
    total = 0
    for name in ACTIVITY_FACT_TABLES:
        count = _safe_count(conn, name)
        total += count
        tables.append({
            "table": name,
            "row_count": count,
            "kind": "fact",
            "category": "analytical_event",
            "origin": "warehouse_activity_fact",
            "classification": classification if count else "unknown",
            "updated_at": _table_max_event_ts(conn, name),
        })

    for row in tables:
        row["pct_of_total"] = round((row["row_count"] / total) * 100.0, 2) if total else 0.0

    class_totals = {c: 0 for c in ("real", "imported", "demo", "synthetic", "unknown")}
    for row in tables:
        class_totals[row["classification"]] = class_totals.get(row["classification"], 0) + row["row_count"]

    updated_candidates = [t["updated_at"] for t in tables if t.get("updated_at")]
    if load and load.get("fecha_carga") is not None:
        fc = load["fecha_carga"]
        updated_candidates.append(fc.isoformat() if hasattr(fc, "isoformat") else str(fc))

    return {
        "total_events": total,
        "formula": "SUM(COUNT(*)) over ACTIVITY_FACT_TABLES",
        "activity_fact_tables": list(ACTIVITY_FACT_TABLES),
        "tables": tables,
        "classification_totals": class_totals,
        "classification_basis": (
            "table-level from latest ctl_carga_dataset.modo; "
            "no per-row provenance columns on activity facts"
        ),
        "latest_load": {
            "modo": load.get("modo") if load else None,
            "estado": load.get("estado") if load else None,
            "fecha_carga": (
                load["fecha_carga"].isoformat()
                if load and load.get("fecha_carga") is not None and hasattr(load["fecha_carga"], "isoformat")
                else (str(load["fecha_carga"]) if load and load.get("fecha_carga") is not None else None)
            ),
            "total_raw": load.get("total_raw") if load else None,
        },
        "updated_at": max(updated_candidates) if updated_candidates else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tooltip": (
            "Reproducciones, sesiones e interacciones generadas a partir de "
            "canciones, artistas y álbumes importados."
        ),
    }
