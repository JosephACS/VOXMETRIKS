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
from ..text_search import fold_text, search_tokens


def _fuzzy_track_filter(query: str) -> Tuple[str, List[Any]]:
    """Small typo fallback used only after the indexed token search is empty.

    DuckDB evaluates the similarity over the catalog columns in one vectorized
    pass.  Keeping this out of the normal search path preserves the fast prefix
    lookup for correctly written queries while still recovering common one or
    two-character mistakes.
    """
    folded = fold_text(query)
    if len(folded.replace(" ", "")) < 4:
        return "1=0", []

    # `lower()` is deliberate here: nested accent replacement over the complete
    # 89k catalog made the fallback feel slow. Jaro-Winkler already tolerates an
    # accent as a single-character difference.
    title = "lower(COALESCE(dt.nombre_track, ''))"
    artist = "lower(COALESCE(da.nombre_artista, ''))"
    combined = f"trim({title} || ' ' || {artist})"
    tokens = search_tokens(query)
    anchor = max(tokens, key=len, default=folded.replace(" ", ""))
    anchors = [anchor[:2], anchor[-2:]] if len(anchor) >= 4 else [anchor[:1]]
    anchors = list(dict.fromkeys(a for a in anchors if a))
    gate = "(" + " OR ".join(f"{combined} LIKE ?" for _ in anchors) + ")"
    score = (
        "greatest("
        f"jaro_winkler_similarity({title}, ?), "
        f"jaro_winkler_similarity({artist}, ?), "
        f"jaro_winkler_similarity({combined}, ?)"
        ")"
    )
    # Short queries need a tighter threshold to avoid noisy matches.
    threshold = 0.86 if len(folded) <= 6 else 0.78
    return (
        f"{gate} AND {score} >= ?",
        [*(f"%{anchor}%" for anchor in anchors), folded, folded, folded, threshold],
    )


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


def search_tracks_fuzzy(
    conn: duckdb.DuckDBPyConnection,
    q: str,
    limit: int = 20,
    page: int = 1,
    *,
    playable_only: bool = True,
) -> Tuple[List[Dict[str, Any]], int]:
    """Return typo-tolerant matches after an exact/token search returned none."""
    fuzzy_sql, fuzzy_params = _fuzzy_track_filter(q)
    vis = public_track_visibility_sql(conn)
    playable = playable_track_sql(conn) if playable_only else "1=1"
    where = f"({fuzzy_sql}) AND ({vis}) AND ({playable})"
    lim = max(1, min(int(limit), 100))
    total = int(conn.execute(track_list_count_sql(where), fuzzy_params).fetchone()[0])
    offset = max(0, (page - 1) * lim)
    rows_raw = conn.execute(
        select_track_list_sql(where) + " LIMIT ? OFFSET ?",
        fuzzy_params + [lim, offset],
    ).fetchall()
    return rows_to_tracks(rows_raw), total
