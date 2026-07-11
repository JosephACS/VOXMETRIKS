"""Extract audio feature vectors and user taste centroids."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import duckdb

from ._helpers import table_exists_conn

AUDIO_FEATURES = (
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
)
TEMPO_KEY = "tempo"
TEMPO_NORM = 200.0


@dataclass
class TrackFeatures:
    track_id: int
    vector: List[float]
    raw: Dict[str, Any] = field(default_factory=dict)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def track_vector(row: Dict[str, Any]) -> List[float]:
    vec = [_safe_float(row.get(k)) for k in AUDIO_FEATURES]
    tempo = _safe_float(row.get(TEMPO_KEY), 120.0)
    vec.append(min(1.0, tempo / TEMPO_NORM))
    return vec


def fetch_track_features(
    conn: duckdb.DuckDBPyConnection, track_ids: Sequence[int]
) -> Dict[int, TrackFeatures]:
    if not track_ids or not table_exists_conn(conn, "dim_track"):
        return {}
    placeholders = ",".join("?" * len(track_ids))
    cols = ", ".join(["id_track", "nombre_track", "id_artista", "id_genero", "popularity"]
                      + list(AUDIO_FEATURES) + [TEMPO_KEY])
    rows = conn.execute(
        f"SELECT {cols} FROM dim_track WHERE id_track IN ({placeholders})",
        list(track_ids),
    ).fetchall()
    names = [d[0] for d in conn.description]
    out: Dict[int, TrackFeatures] = {}
    for row in rows:
        d = dict(zip(names, row))
        tid = int(d["id_track"])
        out[tid] = TrackFeatures(track_id=tid, vector=track_vector(d), raw=d)
    return out


def centroid(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return [0.0] * (len(AUDIO_FEATURES) + 1)
    dim = len(vectors[0])
    acc = [0.0] * dim
    for v in vectors:
        for i in range(dim):
            acc[i] += v[i]
    n = len(vectors)
    return [x / n for x in acc]


def audio_dna_profile(centroid_vec: List[float]) -> Dict[str, int]:
    """Human-readable audio DNA percentages."""
    if not centroid_vec:
        return {}
    d, e, _, ac, inst, _, v = centroid_vec[:7]
    return {
        "energetic": min(100, max(0, int(e * 100))),
        "dance": min(100, max(0, int(d * 100))),
        "acoustic": min(100, max(0, int(ac * 100))),
        "instrumental": min(100, max(0, int(inst * 100))),
        "positive": min(100, max(0, int(v * 100))),
    }


def load_user_signal_tracks(
    conn: duckdb.DuckDBPyConnection, app_user_id: int, wh_user_id: int
) -> List[int]:
    """Favorite + warehouse played track ids for taste modeling."""
    ids: List[int] = []
    try:
        fav_rows = conn.execute(
            "SELECT track_id FROM app_favorite WHERE user_id = ? ORDER BY added_at DESC LIMIT 50",
            [app_user_id],
        ).fetchall()
        ids.extend(int(r[0]) for r in fav_rows)
    except Exception:
        pass

    events = "silver_streams" if table_exists_conn(conn, "silver_streams") else "fact_streaming"
    if table_exists_conn(conn, events):
        try:
            play_rows = conn.execute(
                f"""
                SELECT id_track, COUNT(*) AS c
                FROM {events}
                WHERE id_usuario = ? AND id_track IS NOT NULL
                GROUP BY id_track
                ORDER BY c DESC
                LIMIT 80
                """,
                [wh_user_id],
            ).fetchall()
            ids.extend(int(r[0]) for r in play_rows)
        except Exception:
            pass

    seen: set[int] = set()
    unique: List[int] = []
    for tid in ids:
        if tid not in seen:
            seen.add(tid)
            unique.append(tid)
    return unique
