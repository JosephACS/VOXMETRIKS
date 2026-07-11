"""Content-based similarity via cosine distance on audio feature vectors."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

import duckdb

from ._helpers import table_exists_conn

from .feature_extractor import AUDIO_FEATURES, TEMPO_KEY, fetch_track_features, track_vector


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def similar_tracks(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    limit: int = 12,
    exclude_ids: Optional[set[int]] = None,
) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "dim_track"):
        return []
    exclude_ids = exclude_ids or set()
    exclude_ids.add(track_id)

    source = fetch_track_features(conn, [track_id]).get(track_id)
    if not source:
        return []

    cols = ", ".join(
        ["dt.id_track", "dt.nombre_track", "da.nombre_artista", "dt.popularity"]
        + [f"dt.{k}" for k in AUDIO_FEATURES]
        + [f"dt.{TEMPO_KEY}"]
    )
    rows = conn.execute(
        f"""
        SELECT {cols}
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track != ?
        ORDER BY dt.popularity DESC NULLS LAST
        LIMIT 400
        """,
        [track_id],
    ).fetchall()
    names = [d[0] for d in conn.description]

    scored: List[tuple[float, Dict[str, Any]]] = []
    for row in rows:
        d = dict(zip(names, row))
        tid = int(d["id_track"])
        if tid in exclude_ids:
            continue
        sim = cosine_similarity(source.vector, track_vector(d))
        if sim < 0.55:
            continue
        scored.append(
            (
                sim,
                {
                    "id_track": tid,
                    "nombre_track": d.get("nombre_track"),
                    "nombre_artista": d.get("nombre_artista"),
                    "popularity": d.get("popularity"),
                    "similarity": round(sim, 4),
                },
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def similar_artists(
    conn: duckdb.DuckDBPyConnection,
    artist_id: int,
    *,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "dim_track"):
        return []

    profile = conn.execute(
        f"""
        SELECT dt.id_genero,
               AVG(dt.energy) AS energy,
               AVG(dt.danceability) AS danceability,
               AVG(dt.valence) AS valence,
               AVG(dt.acousticness) AS acousticness,
               AVG(dt.instrumentalness) AS instrumentalness,
               AVG(dt.tempo) AS tempo,
               COUNT(*) AS track_count
        FROM dim_track dt
        WHERE dt.id_artista = ?
        GROUP BY dt.id_genero
        """,
        [artist_id],
    ).fetchone()
    if not profile:
        return []

    genre_id = profile[0]
    vec = track_vector(
        {
            "energy": profile[1],
            "danceability": profile[2],
            "valence": profile[3],
            "acousticness": profile[4],
            "instrumentalness": profile[5],
            "tempo": profile[6],
        }
    )

    rows = conn.execute(
        f"""
        SELECT da.id_artista, da.nombre_artista, dt.id_genero,
               AVG(dt.energy) AS energy,
               AVG(dt.danceability) AS danceability,
               AVG(dt.valence) AS valence,
               AVG(dt.acousticness) AS acousticness,
               AVG(dt.instrumentalness) AS instrumentalness,
               AVG(dt.tempo) AS tempo,
               MAX(dt.popularity) AS max_pop
        FROM dim_artista da
        INNER JOIN dim_track dt ON dt.id_artista = da.id_artista
        WHERE da.id_artista != ?
        GROUP BY da.id_artista, da.nombre_artista, dt.id_genero
        HAVING COUNT(*) >= 2
        ORDER BY max_pop DESC NULLS LAST
        LIMIT 120
        """,
        [artist_id],
    ).fetchall()

    scored: List[tuple[float, Dict[str, Any]]] = []
    for row in rows:
        aid, name, gid, e, d, v, ac, inst, tempo, max_pop = row
        artist_vec = track_vector(
            {
                "energy": e,
                "danceability": d,
                "valence": v,
                "acousticness": ac,
                "instrumentalness": inst,
                "tempo": tempo,
            }
        )
        sim = cosine_similarity(vec, artist_vec)
        genre_bonus = 0.12 if genre_id and gid == genre_id else 0.0
        score = sim + genre_bonus
        scored.append(
            (
                score,
                {
                    "id_artista": int(aid),
                    "nombre_artista": name,
                    "similarity": round(sim, 4),
                    "same_genre": bool(genre_id and gid == genre_id),
                    "popularity": int(max_pop or 0),
                },
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
