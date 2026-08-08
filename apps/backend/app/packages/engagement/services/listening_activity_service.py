# -*- coding: utf-8 -*-
"""Personal listening activity aggregations — app_listening_history only (spec 035)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from app.core.database import table_exists
from app.packages.catalog.services.display_text import clean_catalog_rows
from app.packages.catalog.services.tracks.playback_availability import (
    playback_status_for_cache,
)
from app.packages.engagement.services.listening_history_service import (
    LISTEN_THRESHOLD_MS,
    SHORT_TRACK_MS,
    ensure_listening_history_table,
)

PERIODS = frozenset({"7d", "30d", "90d", "all"})

_VALID_SQL = f"""
(
  h.completed = TRUE
  OR h.listened_ms >= {LISTEN_THRESHOLD_MS}
  OR (
    dt.duration_ms IS NOT NULL
    AND dt.duration_ms > 0
    AND dt.duration_ms < {SHORT_TRACK_MS}
    AND h.listened_ms >= CAST(dt.duration_ms * 0.5 AS INTEGER)
  )
)
"""


def _playback_status(conn: duckdb.DuckDBPyConnection, track_id: int) -> str:
    if not table_exists(conn, "app_track_audio_source"):
        return playback_status_for_cache(None)
    try:
        row = conn.execute(
            """
            SELECT status, failure_count
            FROM app_track_audio_source
            WHERE track_id = ?
            LIMIT 1
            """,
            [int(track_id)],
        ).fetchone()
    except Exception:
        return playback_status_for_cache(None)
    if not row:
        return playback_status_for_cache(None)
    return playback_status_for_cache(
        {"status": row[0], "failure_count": row[1]}
    )


def parse_period(period: str) -> str:
    p = (period or "30d").strip().lower()
    if p not in PERIODS:
        raise ValueError("invalid_period")
    return p


def period_bounds(period: str) -> Tuple[Optional[datetime], datetime, str]:
    """Return (from_utc inclusive, to_utc exclusive-ish now, label)."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    p = parse_period(period)
    if p == "all":
        return None, now, "all"
    days = {"7d": 7, "30d": 30, "90d": 90}[p]
    start = now - timedelta(days=days)
    return start, now, p


def _period_filter_sql(period: str) -> Tuple[str, List[Any]]:
    start, _now, p = period_bounds(period)
    if start is None:
        return "1=1", []
    return "h.played_at >= ?", [start]


def get_listening_activity(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    period: str = "30d",
    top_limit: int = 10,
    recent_limit: int = 25,
) -> Dict[str, Any]:
    """
    Consolidated personal activity for the authenticated user only.
    Never accepts another user's id from the client — caller must pass session user_id.
    """
    ensure_listening_history_table(conn)
    uid = int(user_id)
    p = parse_period(period)
    start, end, p_label = period_bounds(p)
    top_n = max(1, min(int(top_limit), 50))
    recent_n = max(1, min(int(recent_limit), 50))
    where_period, period_params = _period_filter_sql(p)

    base_from = f"""
      FROM app_listening_history h
      JOIN dim_track dt ON dt.id_track = h.track_id
      LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
      LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
      WHERE h.user_id = ?
        AND {_VALID_SQL}
        AND ({where_period})
    """
    params: List[Any] = [uid, *period_params]

    # Summary
    summary_row = conn.execute(
        f"""
        SELECT
          COUNT(*) AS plays,
          COUNT(DISTINCT h.track_id) AS tracks,
          COUNT(DISTINCT dt.id_artista) AS artists,
          COALESCE(SUM(h.listened_ms), 0) AS listened_ms,
          COUNT(DISTINCT CAST(h.played_at AS DATE)) AS active_days
        {base_from}
        """,
        params,
    ).fetchone()
    plays = int(summary_row[0] or 0)
    listened_ms = int(summary_row[3] or 0)
    summary = {
        "plays": plays,
        "distinct_tracks": int(summary_row[1] or 0),
        "distinct_artists": int(summary_row[2] or 0),
        "listened_ms": listened_ms,
        "listened_minutes": round(listened_ms / 60_000, 1),
        "active_days": int(summary_row[4] or 0),
    }
    empty = plays == 0

    # Top tracks
    track_rows = conn.execute(
        f"""
        SELECT
          h.track_id,
          ANY_VALUE(dt.nombre_track),
          ANY_VALUE(da.nombre_artista),
          ANY_VALUE(dt.id_artista),
          ANY_VALUE(dt.duration_ms),
          COUNT(*) AS play_count,
          COALESCE(SUM(h.listened_ms), 0) AS listened_ms
        {base_from}
        GROUP BY h.track_id
        ORDER BY play_count DESC, listened_ms DESC
        LIMIT ?
        """,
        [*params, top_n],
    ).fetchall()
    top_tracks = []
    for i, r in enumerate(track_rows, start=1):
        tid = int(r[0])
        status = _playback_status(conn, tid)
        top_tracks.append(
            {
                "rank": i,
                "id_track": tid,
                "nombre_track": r[1],
                "nombre_artista": r[2],
                "id_artista": int(r[3]) if r[3] is not None else None,
                "duration_ms": int(r[4]) if r[4] is not None else None,
                "plays": int(r[5]),
                "listened_ms": int(r[6] or 0),
                "playback_status": status,
                "source_unavailable": status != "playable",
            }
        )

    # Top artists (primary artist id only)
    artist_rows = conn.execute(
        f"""
        SELECT
          dt.id_artista,
          ANY_VALUE(da.nombre_artista),
          COUNT(*) AS play_count,
          COALESCE(SUM(h.listened_ms), 0) AS listened_ms,
          COUNT(DISTINCT h.track_id) AS tracks
        {base_from}
          AND dt.id_artista IS NOT NULL
        GROUP BY dt.id_artista
        ORDER BY play_count DESC, listened_ms DESC
        LIMIT ?
        """,
        [*params, top_n],
    ).fetchall()
    top_artists = [
        {
            "rank": i,
            "id_artista": int(r[0]),
            "nombre_artista": r[1],
            "plays": int(r[2]),
            "listened_ms": int(r[3] or 0),
            "listened_minutes": round(int(r[3] or 0) / 60_000, 1),
            "distinct_tracks": int(r[4] or 0),
        }
        for i, r in enumerate(artist_rows, start=1)
    ]

    # Top genres (primary genre only — one count per play)
    genre_rows = conn.execute(
        f"""
        SELECT
          dt.id_genero,
          ANY_VALUE(dg.nombre_genero),
          COUNT(*) AS play_count,
          COALESCE(SUM(h.listened_ms), 0) AS listened_ms
        {base_from}
          AND dt.id_genero IS NOT NULL
        GROUP BY dt.id_genero
        ORDER BY play_count DESC, listened_ms DESC
        LIMIT ?
        """,
        [*params, top_n],
    ).fetchall()
    genre_total = sum(int(r[2]) for r in genre_rows) or 1
    top_genres = [
        {
            "rank": i,
            "id_genero": int(r[0]),
            "nombre_genero": r[1],
            "plays": int(r[2]),
            "listened_ms": int(r[3] or 0),
            "share_pct": round(100.0 * int(r[2]) / genre_total, 1),
        }
        for i, r in enumerate(genre_rows, start=1)
    ]

    # Timeline by day
    timeline_rows = conn.execute(
        f"""
        SELECT
          CAST(h.played_at AS DATE) AS day,
          COUNT(*) AS plays,
          COALESCE(SUM(h.listened_ms), 0) AS listened_ms
        {base_from}
        GROUP BY CAST(h.played_at AS DATE)
        ORDER BY day ASC
        """,
        params,
    ).fetchall()
    timeline = [
        {
            "date": str(r[0]),
            "plays": int(r[1]),
            "listened_ms": int(r[2] or 0),
            "listened_minutes": round(int(r[2] or 0) / 60_000, 1),
        }
        for r in timeline_rows
    ]

    # Recent (valid only, independent limit)
    recent_rows = conn.execute(
        f"""
        SELECT
          h.id, h.track_id, h.played_at, h.listened_ms, h.completed,
          dt.nombre_track, da.nombre_artista, dt.duration_ms, dt.id_artista
        {base_from}
        ORDER BY h.played_at DESC
        LIMIT ?
        """,
        [*params, recent_n],
    ).fetchall()
    recent = []
    for r in recent_rows:
        tid = int(r[1])
        status = _playback_status(conn, tid)
        recent.append(
            {
                "id": int(r[0]),
                "id_track": tid,
                "played_at": str(r[2]) if r[2] else None,
                "listened_ms": int(r[3] or 0),
                "completed": bool(r[4]),
                "nombre_track": r[5],
                "nombre_artista": r[6],
                "duration_ms": int(r[7]) if r[7] is not None else None,
                "id_artista": int(r[8]) if r[8] is not None else None,
                "playback_status": status,
                "source_unavailable": status != "playable",
            }
        )

    payload = {
        "period": p_label,
        "period_start": start.isoformat(sep=" ") if start else None,
        "period_end": end.isoformat(sep=" "),
        "timezone": "UTC",
        "empty": empty,
        "message": (
            "Aún no tienes suficiente actividad. Escucha algunas canciones y vuelve más tarde."
            if empty
            else ""
        ),
        "rules": {
            "valid_listen": "≥30s or ≥50% when track duration < 60s",
            "artist_grouping": "primary id_artista only",
            "genre_grouping": "primary id_genero only (one count per play)",
            "data_source": "app_listening_history",
            "excludes": ["fact_streaming", "warehouse_synthetic"],
        },
        "summary": summary,
        "top_tracks": clean_catalog_rows(top_tracks),
        "top_artists": clean_catalog_rows(top_artists),
        "top_genres": clean_catalog_rows(top_genres),
        "timeline": timeline,
        "recent": clean_catalog_rows(recent),
    }
    return payload
