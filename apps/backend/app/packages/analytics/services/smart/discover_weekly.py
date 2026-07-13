"""Discover Weekly — personalized weekly playlist."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id
from ._helpers import table_exists_conn

from .ranking_engine import RankingEngine

DISCOVER_WEEKLY_CODE = "discover_weekly"


def _week_seed(user_id: int) -> int:
    week = datetime.now(timezone.utc).isocalendar()[1]
    year = datetime.now(timezone.utc).year
    raw = f"{user_id}-{year}-W{week}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def build_discover_weekly(
    conn: duckdb.DuckDBPyConnection, app_user_id: int, *, limit: int = 30
) -> Dict[str, Any]:
    wh_user = _warehouse_user_id(app_user_id)
    ranker = RankingEngine(conn)
    base = ranker.rank_for_user(app_user_id, wh_user, limit=limit * 2)

    seed = _week_seed(app_user_id)
    known_artists: Set[int] = set()
    if table_exists_conn(conn, "dim_track"):
        rows = conn.execute(
            """
            SELECT DISTINCT dt.id_artista
            FROM app_favorite f
            INNER JOIN dim_track dt ON dt.id_track = f.track_id
            WHERE f.user_id = ? AND dt.id_artista IS NOT NULL
            """,
            [app_user_id],
        ).fetchall()
        known_artists = {int(r[0]) for r in rows}

    mixed: List[Dict[str, Any]] = []
    new_artists: List[Dict[str, Any]] = []
    familiar: List[Dict[str, Any]] = []

    for item in base:
        tid = item["id_track"]
        artist_row = conn.execute(
            "SELECT id_artista, id_genero FROM dim_track WHERE id_track = ?",
            [tid],
        ).fetchone()
        artist_id = int(artist_row[0]) if artist_row and artist_row[0] else None
        if artist_id and artist_id in known_artists:
            familiar.append({**item, "mix_tag": "familiar_artist"})
        else:
            new_artists.append({**item, "mix_tag": "new_discovery"})

    i = seed % max(1, len(base) or 1)
    while len(mixed) < limit and (familiar or new_artists or base):
        if len(mixed) % 3 != 2 and familiar:
            mixed.append(familiar.pop(0))
        elif new_artists:
            mixed.append(new_artists.pop(0))
        elif familiar:
            mixed.append(familiar.pop(0))
        elif base:
            mixed.append({**base[i % len(base)], "mix_tag": "trending"})
            i += 1
        else:
            break

    week = datetime.now(timezone.utc).isocalendar()
    return {
        "playlist_id": f"discover-weekly-{app_user_id}",
        "code": DISCOVER_WEEKLY_CODE,
        "week": f"{week[0]}-W{week[1]:02d}",
        "track_count": len(mixed),
        "tracks": mixed[:limit],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
