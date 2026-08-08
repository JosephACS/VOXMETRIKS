"""Offset and cursor-paginated track listing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from app.core.pagination import (
    decode_track_cursor,
    encode_track_cursor,
    track_cursor_predicate,
)

from .queries import (
    build_list_conditions,
    rows_to_tracks,
    select_track_list_sql,
    track_list_count_sql,
    where_clause,
)
from .visibility import public_track_visibility_sql
from .playback_availability import playable_track_sql


def get_tracks(
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    artist_id: Optional[int] = None,
    *,
    playable_only: bool = True,
) -> Tuple[List[Dict[str, Any]], int]:
    """List tracks with artist/genre names joined (same shape as search/detail)."""
    offset = (page - 1) * limit
    conditions, params = build_list_conditions(
        conn, search=search, genre_id=genre_id, artist_id=artist_id,
    )
    conditions.append(public_track_visibility_sql(conn))
    if playable_only:
        conditions.append(playable_track_sql(conn))
    where = where_clause(conditions)
    total = int(conn.execute(track_list_count_sql(where), params).fetchone()[0])

    data_sql = select_track_list_sql(where) + " LIMIT ? OFFSET ?"
    rows_raw = conn.execute(data_sql, params + [limit, offset]).fetchall()
    return rows_to_tracks(rows_raw), total


def get_tracks_cursor(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    cursor: Optional[str] = None,
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    artist_id: Optional[int] = None,
    include_total: bool = False,
    playable_only: bool = True,
) -> Dict[str, Any]:
    """Keyset-paginated track list (popularity DESC, id_track ASC)."""
    lim = max(1, min(int(limit), 500))
    conditions, params = build_list_conditions(
        conn, search=search, genre_id=genre_id, artist_id=artist_id,
    )
    conditions.append(public_track_visibility_sql(conn))
    if playable_only:
        conditions.append(playable_track_sql(conn))

    if cursor:
        try:
            cursor_pop, cursor_id = decode_track_cursor(cursor)
        except ValueError as exc:
            raise ValueError("Invalid cursor") from exc
        conditions.append(track_cursor_predicate())
        params.extend([cursor_pop, cursor_pop, cursor_id])

    where = where_clause(conditions)
    rows_raw = conn.execute(
        select_track_list_sql(where) + " LIMIT ?",
        params + [lim + 1],
    ).fetchall()
    has_more = len(rows_raw) > lim
    page_rows = rows_raw[:lim]
    items = rows_to_tracks(page_rows)

    next_cursor: Optional[str] = None
    if has_more and page_rows:
        last = page_rows[-1]
        next_cursor = encode_track_cursor(last[8], int(last[0]))

    total: Optional[int] = None
    if include_total and not cursor:
        total = int(conn.execute(track_list_count_sql(where), params).fetchone()[0])

    return {
        "items": items,
        "limit": lim,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total": total,
    }
