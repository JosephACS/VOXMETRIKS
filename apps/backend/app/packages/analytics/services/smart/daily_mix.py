"""Daily Mix playlists by genre cluster."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id
from ._helpers import table_exists_conn

from .feature_extractor import load_user_signal_tracks
from .ranking_engine import RankingEngine

MIX_DEFINITIONS = (
    ("daily-mix-rock", "Daily Mix Rock", {"energy_min": 0.55, "acousticness_max": 0.45}),
    ("daily-mix-pop", "Daily Mix Pop", {"danceability_min": 0.55, "energy_min": 0.4}),
    ("daily-mix-chill", "Daily Mix Chill", {"energy_max": 0.45, "valence_min": 0.3}),
    ("daily-mix-instrumental", "Daily Mix Instrumental", {"instrumentalness_min": 0.5}),
)


def build_daily_mixes(
    conn: duckdb.DuckDBPyConnection, app_user_id: int, *, limit: int = 20
) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "dim_track"):
        return []

    wh_user = _warehouse_user_id(app_user_id)
    ranker = RankingEngine(conn)
    pool = ranker.rank_for_user(app_user_id, wh_user, limit=200)
    pool_ids = [p["id_track"] for p in pool]

    if not pool_ids:
        return []

    placeholders = ",".join("?" * len(pool_ids))
    rows = conn.execute(
        f"""
        SELECT dt.id_track, dt.nombre_track, da.nombre_artista,
               dt.energy, dt.danceability, dt.valence,
               dt.acousticness, dt.instrumentalness, dt.popularity
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track IN ({placeholders})
        """,
        pool_ids,
    ).fetchall()
    names = [d[0] for d in conn.description]
    catalog = {int(dict(zip(names, r))["id_track"]): dict(zip(names, r)) for r in rows}

    mixes: List[Dict[str, Any]] = []
    for mix_id, title, rules in MIX_DEFINITIONS:
        tracks: List[Dict[str, Any]] = []
        for pid in pool_ids:
            row = catalog.get(pid)
            if not row:
                continue
            if not _matches_rules(row, rules):
                continue
            tracks.append(
                {
                    "id_track": int(row["id_track"]),
                    "nombre_track": row.get("nombre_track"),
                    "nombre_artista": row.get("nombre_artista"),
                    "popularity": row.get("popularity"),
                }
            )
            if len(tracks) >= limit:
                break
        if tracks:
            mixes.append(
                {
                    "playlist_id": f"{mix_id}-{app_user_id}",
                    "title": title,
                    "track_count": len(tracks),
                    "tracks": tracks,
                }
            )
    return mixes


def _matches_rules(row: Dict[str, Any], rules: Dict[str, float]) -> bool:
    for key, threshold in rules.items():
        if key.endswith("_min"):
            feat = key.replace("_min", "")
            if float(row.get(feat) or 0) < threshold:
                return False
        elif key.endswith("_max"):
            feat = key.replace("_max", "")
            if float(row.get(feat) or 0) > threshold:
                return False
    return True
