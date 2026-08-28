"""Precomputed accent-folded search haystack for catalog tracks."""

from __future__ import annotations

import logging

import duckdb

from app.core.database import get_table_columns, table_exists
from app.packages.streaming.services.text_search import fold_text

logger = logging.getLogger("voxmetrik.search_fold")


def _row_search_fold(
    track_name: str | None,
    artist_name: str | None,
    genre_name: str | None,
) -> str:
    parts = [
        fold_text(track_name or ""),
        fold_text(artist_name or ""),
        fold_text(genre_name or ""),
    ]
    return " ".join(p for p in parts if p).strip()


def ensure_search_fold(conn: duckdb.DuckDBPyConnection) -> None:
    """Add ``search_fold`` to dim_track, backfill, and create supporting index."""
    if not table_exists(conn, "dim_track"):
        return

    cols = set(get_table_columns(conn, "dim_track"))
    if "search_fold" not in cols:
        conn.execute("ALTER TABLE dim_track ADD COLUMN search_fold VARCHAR")

    pending = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM dim_track dt
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
            WHERE dt.search_fold IS NULL OR TRIM(dt.search_fold) = ''
            """
        ).fetchone()[0]
    )
    if pending:
        # DuckDB can reject an UPDATE on an indexed table with a misleading
        # duplicate-primary-key error while the secondary index is present.
        # Rebuild the optional search index after the small incremental backfill.
        try:
            conn.execute("DROP INDEX IF EXISTS idx_dim_track_search_fold")
        except Exception as exc:
            logger.warning("search_fold index could not be prepared for backfill: %s", exc)
        rows = conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista, dg.nombre_genero
            FROM dim_track dt
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
            WHERE dt.search_fold IS NULL OR TRIM(dt.search_fold) = ''
            """
        ).fetchall()
        for track_id, nombre, artista, genero in rows:
            folded = _row_search_fold(nombre, artista, genero)
            conn.execute(
                "UPDATE dim_track SET search_fold = ? WHERE id_track = ?",
                [folded, int(track_id)],
            )
        logger.info("Backfilled search_fold for %s tracks", len(rows))

    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dim_track_search_fold ON dim_track(search_fold)"
        )
    except Exception as exc:
        logger.warning("search_fold index skipped: %s", exc)
