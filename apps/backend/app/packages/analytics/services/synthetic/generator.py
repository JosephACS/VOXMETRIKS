"""Orchestration for synthetic activity generation."""

from __future__ import annotations

import logging
from typing import Any, Dict

import duckdb

from app.core.query_helpers import count_rows

from ..stats.constants import (
    ACTIVITY_FACT_TABLES,
    MAX_CREATE_PER_RUN,
    MAX_TARGET_TOTAL,
    SYNTHETIC_BATCH_SIZE,
    WARN_CREATE_ABOVE,
)
from .dimensions import (
    ensure_activity_dimensions,
    purge_synthetic_catalog,
    refresh_enterprise_aggregates,
    split_activity_counts,
)
from .facts import (
    real_track_count,
    replace_fact_favorites,
    replace_fact_playlist_activity,
    replace_fact_searches,
    replace_fact_stream_sessions,
    replace_fact_streaming,
    replace_fact_user_activity,
)

logger = logging.getLogger(__name__)


def get_synthetic_limits() -> Dict[str, Any]:
    """Límites expuestos al frontend para validación antes de generar."""
    return {
        "max_target_total": MAX_TARGET_TOTAL,
        "max_create_per_run": MAX_CREATE_PER_RUN,
        "warn_create_above": WARN_CREATE_ABOVE,
        "batch_size": SYNTHETIC_BATCH_SIZE,
        "duckdb_note": (
            "DuckDB soporta millones de eventos. El catálogo musical se mantiene real; "
            "lo sintético se genera en streams, búsquedas, favoritos, playlists y sesiones."
        ),
    }


def _activity_total(conn: duckdb.DuckDBPyConnection) -> int:
    return sum(count_rows(conn, table) for table in ACTIVITY_FACT_TABLES)


def generate_synthetic_activity(
    conn: duckdb.DuckDBPyConnection,
    *,
    target_total: int | None = None,
    multiplier: int | None = None,
) -> Dict[str, Any]:
    """
    Generate high-volume behavioral activity over real catalog rows.

    Musical catalog tables (dim_track, dim_artista, dim_album, dim_genero) stay real.
    Synthetic data is limited to users/playlists and activity facts.
    """
    if target_total is None and multiplier is None:
        raise ValueError("provide target_total or multiplier")

    purged_tracks = purge_synthetic_catalog(conn)
    real_tracks = real_track_count(conn)
    if real_tracks == 0:
        raise ValueError(
            "No hay tracks reales en el warehouse. Importa primero desde PocketBase "
            "(POST /api/v1/stats/import o python scripts/import_from_pocketbase.py)."
        )

    before = _activity_total(conn)
    if target_total is None:
        if multiplier is None or multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        target_total = before * multiplier

    if target_total < 1:
        raise ValueError("target_total must be >= 1")
    if target_total > MAX_TARGET_TOTAL:
        raise ValueError(
            f"target_total cannot exceed {MAX_TARGET_TOTAL:,} "
            f"(DuckDB límite del proyecto; pediste {target_total:,})"
        )

    created = max(0, target_total - before)
    if created == 0:
        return {
            "before": before,
            "after": before,
            "created": 0,
            "target_total": target_total,
            "source_rows": real_tracks,
            "track_total": real_tracks,
            "purged_synthetic_tracks": purged_tracks,
            "batches": 0,
            "warning": None,
        }

    if created > MAX_CREATE_PER_RUN:
        raise ValueError(
            f"cannot create more than {MAX_CREATE_PER_RUN:,} rows in one run "
            f"(requested {created:,}). Usa varias ejecuciones (+100K) o baja el objetivo."
        )

    dimensions = ensure_activity_dimensions(conn, target_total)
    activity_counts = split_activity_counts(target_total)
    replace_fact_streaming(conn, activity_counts["fact_streaming"])
    replace_fact_user_activity(conn, activity_counts["fact_user_activity"])
    replace_fact_playlist_activity(conn, activity_counts["fact_playlist_activity"])
    replace_fact_favorites(conn, activity_counts["fact_favorites"])
    replace_fact_searches(conn, activity_counts["fact_searches"])
    replace_fact_stream_sessions(conn, activity_counts["fact_stream_sessions"])
    refresh_enterprise_aggregates(conn)

    after = _activity_total(conn)
    created = max(0, after - before)
    warning = "large" if created >= WARN_CREATE_ABOVE else None

    try:
        id_carga = conn.execute(
            "SELECT COALESCE(MAX(id_carga), 0) + 1 FROM ctl_carga_dataset"
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO ctl_carga_dataset
                (id_carga, fecha_carga, modo, registros_nuevos, total_raw, estado)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, 'OK')
            """,
            [id_carga, f"synthetic_activity_target_{target_total}", created, after],
        )
    except Exception:
        logger.exception("synthetic activity: ctl_carga_dataset insert failed")

    return {
        "before": before,
        "after": after,
        "created": created,
        "target_total": target_total,
        "source_rows": real_tracks,
        "track_total": real_tracks,
        "purged_synthetic_tracks": purged_tracks,
        "dimensions": dimensions,
        "activity_counts": activity_counts,
        "batches": max(1, (target_total + SYNTHETIC_BATCH_SIZE - 1) // SYNTHETIC_BATCH_SIZE),
        "warning": warning,
    }


generate_synthetic_tracks = generate_synthetic_activity
