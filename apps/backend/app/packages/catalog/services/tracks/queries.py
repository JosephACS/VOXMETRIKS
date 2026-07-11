"""Shared SQL builders and row mapping for track list queries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from app.core.database import get_table_columns

from ..display_text import clean_catalog_row, clean_catalog_rows
from ..text_search import build_track_search_filter
from .columns import DETAIL_COLS, TRACK_LIST_COLS


def track_search_filter(
    conn: duckdb.DuckDBPyConnection,
    query: str,
) -> Tuple[str, List[Any]]:
    q = query.strip()
    cols = set(get_table_columns(conn, "dim_track"))
    if "search_fold" in cols:
        return build_track_search_filter(q, search_fold_col="COALESCE(dt.search_fold, '')")
    return build_track_search_filter(q)


def select_track_list_sql(where: str) -> str:
    return f"""
        SELECT
            dt.id_track, dt.spotify_track_id, dt.nombre_track,
            dt.id_artista, dt.id_album, dt.id_genero,
            dt.explicit, dt.duration_ms, dt.popularity,
            da.nombre_artista, dg.nombre_genero
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE {where}
        ORDER BY dt.popularity DESC NULLS LAST, dt.id_track
    """


def track_list_count_sql(where: str) -> str:
    return f"""
        SELECT COUNT(*)
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE {where}
    """


def rows_to_tracks(rows_raw: list) -> List[Dict[str, Any]]:
    return clean_catalog_rows([dict(zip(TRACK_LIST_COLS, row)) for row in rows_raw])


def build_list_conditions(
    conn: duckdb.DuckDBPyConnection,
    *,
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    artist_id: Optional[int] = None,
) -> Tuple[List[str], List[Any]]:
    conditions: List[str] = []
    params: List[Any] = []

    if search:
        search_sql, search_params = track_search_filter(conn, search.strip())
        conditions.append(f"({search_sql})")
        params.extend(search_params)
    if genre_id is not None:
        conditions.append("dt.id_genero = ?")
        params.append(genre_id)
    if artist_id is not None:
        from ..artist_service import get_artist_by_id
        artist = get_artist_by_id(conn, artist_id)
        if artist:
            primary = (artist.get("nombre_artista") or "").split(";")[0].strip()
            conditions.append(
                "(dt.id_artista = ? OR LOWER(da.nombre_artista) LIKE LOWER(?) "
                "OR LOWER(TRIM(SPLIT_PART(REPLACE(da.nombre_artista, ',', ';'), ';', 1))) = LOWER(?))"
            )
            params.extend([artist_id, f"%{primary}%", primary])
        else:
            conditions.append("dt.id_artista = ?")
            params.append(artist_id)

    return conditions, params


def where_clause(conditions: List[str]) -> str:
    return " AND ".join(conditions) if conditions else "1=1"


def map_track_detail_row(row: tuple) -> Dict[str, Any]:
    return clean_catalog_row(dict(zip(DETAIL_COLS, row)))
