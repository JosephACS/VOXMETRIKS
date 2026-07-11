"""Secondary DuckDB indexes for catalog and analytics hot paths."""

from __future__ import annotations

import logging

import duckdb

from .database import table_exists

logger = logging.getLogger("voxmetrik.database")

_INDEX_STATEMENTS: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_dim_track_popularity ON dim_track(popularity)",
    "CREATE INDEX IF NOT EXISTS idx_dim_track_id_artista ON dim_track(id_artista)",
    "CREATE INDEX IF NOT EXISTS idx_dim_track_id_genero ON dim_track(id_genero)",
    "CREATE INDEX IF NOT EXISTS idx_dim_track_id_album ON dim_track(id_album)",
    "CREATE INDEX IF NOT EXISTS idx_dim_artista_nombre ON dim_artista(nombre_artista)",
    "CREATE INDEX IF NOT EXISTS idx_agg_tracks_pop_popularity ON agg_tracks_populares(popularity)",
    "CREATE INDEX IF NOT EXISTS idx_agg_top_artistas_pop ON agg_top_artistas(promedio_popularidad)",
]


def ensure_secondary_indexes(conn: duckdb.DuckDBPyConnection) -> None:
    """Create idempotent secondary indexes; skip missing tables gracefully."""
    for sql in _INDEX_STATEMENTS:
        table = sql.split(" ON ")[1].split("(")[0].strip()
        if not table_exists(conn, table):
            continue
        try:
            conn.execute(sql)
        except Exception as exc:
            logger.warning("Index skipped (%s): %s", sql[:60], exc)
