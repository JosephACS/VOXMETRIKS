"""Track search with offset or cursor pagination."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from app.core.pagination import (
    decode_track_cursor,
    encode_track_cursor,
    track_cursor_predicate,
)

from .queries import (
    rows_to_tracks,
    select_track_list_sql,
    track_list_count_sql,
    track_search_filter,
)
from .visibility import public_track_visibility_sql
from .playback_availability import playable_track_sql


def search_tracks(
    conn: duckdb.DuckDBPyConnection,
    q: str,
    limit: int = 50,
    page: int = 1,
    cursor: Optional[str] = None,
    *,
    playable_only: bool = True,
) -> Tuple[List[Dict[str, Any]], int, Optional[str], bool]:
    """Search tracks by tokens (accent-insensitive). Supports offset page or cursor."""
    search_sql, search_params = track_search_filter(conn, q)
    vis = public_track_visibility_sql(conn)
    playable = playable_track_sql(conn) if playable_only else "1=1"
    lim = max(1, min(int(limit), 100))

    if cursor:
        try:
            cursor_pop, cursor_id = decode_track_cursor(cursor)
        except ValueError as exc:
            raise ValueError("Invalid cursor") from exc
        where = f"({search_sql}) AND ({vis}) AND ({playable}) AND {track_cursor_predicate()}"
        params: List[Any] = search_params + [cursor_pop, cursor_pop, cursor_id]
        rows_raw = conn.execute(
            select_track_list_sql(where) + " LIMIT ?",
            params + [lim + 1],
        ).fetchall()
        has_more = len(rows_raw) > lim
        page_rows = rows_raw[:lim]
        items = rows_to_tracks(page_rows)
        next_cursor = None
        if has_more and page_rows:
            last = page_rows[-1]
            next_cursor = encode_track_cursor(last[8], int(last[0]))
        return items, 0, next_cursor, has_more

    where = f"({search_sql}) AND ({vis}) AND ({playable})"
    total = int(conn.execute(track_list_count_sql(where), search_params).fetchone()[0])
    offset = max(0, (page - 1) * lim)
    rows_raw = conn.execute(
        select_track_list_sql(where) + " LIMIT ? OFFSET ?",
        search_params + [lim, offset],
    ).fetchall()
    return rows_to_tracks(rows_raw), total, None, False
