"""Spotify-seeded recommendations without Spotify's restricted Recommendations API.

Spotify supplies consented taste signals (top, recent and saved track ids).  The
actual ranking stays inside VOXMETRIKS so the feature also works with the local
warehouse, remains explainable and never depends on a removed Web API endpoint.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence

import duckdb

from .feature_extractor import centroid, fetch_track_features
from .ranking_engine import RankingEngine
from .similarity_engine import cosine_similarity


def _unique(values: Iterable[str], *, limit: int = 100) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _spotify_seed_rows(
    conn: duckdb.DuckDBPyConnection,
    weighted_ids: Sequence[tuple[str, float]],
) -> list[dict[str, Any]]:
    if not weighted_ids:
        return []
    ids = _unique((track_id for track_id, _ in weighted_ids))
    if not ids:
        return []
    weights = dict(weighted_ids)
    placeholders = ",".join("?" for _ in ids)
    try:
        rows = conn.execute(
            f"""
            SELECT id_track, spotify_track_id, id_artista, id_genero
            FROM dim_track
            WHERE spotify_track_id IN ({placeholders})
            """,
            ids,
        ).fetchall()
    except Exception:
        return []
    return [
        {
            "id_track": int(row[0]),
            "spotify_track_id": str(row[1]),
            "id_artista": int(row[2]) if row[2] is not None else None,
            "id_genero": int(row[3]) if row[3] is not None else None,
            "weight": float(weights.get(str(row[1]), 0.5)),
        }
        for row in rows
    ]


def _candidate_metadata(
    conn: duckdb.DuckDBPyConnection,
    track_ids: Sequence[int],
) -> dict[int, dict[str, Any]]:
    if not track_ids:
        return {}
    placeholders = ",".join("?" for _ in track_ids)
    rows = conn.execute(
        f"""
        SELECT id_track, spotify_track_id, id_artista, id_genero
        FROM dim_track
        WHERE id_track IN ({placeholders})
        """,
        list(track_ids),
    ).fetchall()
    return {
        int(row[0]): {
            "spotify_track_id": str(row[1]) if row[1] else None,
            "id_artista": int(row[2]) if row[2] is not None else None,
            "id_genero": int(row[3]) if row[3] is not None else None,
        }
        for row in rows
    }


def rank_from_spotify_taste(
    conn: duckdb.DuckDBPyConnection,
    *,
    app_user_id: int,
    warehouse_user_id: int,
    top_track_ids: Sequence[str],
    recent_track_ids: Sequence[str],
    saved_track_ids: Sequence[str],
    limit: int = 20,
) -> Dict[str, Any]:
    """Blend Spotify taste signals with VOX history and warehouse similarity."""

    top = _unique(top_track_ids, limit=50)
    recent = _unique(recent_track_ids, limit=50)
    saved = _unique(saved_track_ids, limit=50)
    weighted_ids = (
        [(track_id, 1.0) for track_id in top]
        + [(track_id, 0.72) for track_id in saved]
        + [(track_id, 0.58) for track_id in recent]
    )
    seeds = _spotify_seed_rows(conn, weighted_ids)
    seed_track_ids = [row["id_track"] for row in seeds]

    # The normal VOX rank already includes local history, favourites, popularity
    # and collaborative signals. Spotify taste is an additional signal, not a
    # replacement for the application's own recommendation engine.
    base = RankingEngine(conn).rank_for_user(
        app_user_id,
        warehouse_user_id,
        limit=max(limit * 4, 40),
        exclude=set(seed_track_ids),
    )
    candidate_ids = [int(item["id_track"]) for item in base]
    metadata = _candidate_metadata(conn, candidate_ids)
    candidate_features = fetch_track_features(conn, candidate_ids)
    seed_features = fetch_track_features(conn, seed_track_ids)
    taste_centroid = centroid(
        [seed_features[track_id].vector for track_id in seed_track_ids if track_id in seed_features]
    )

    artist_affinity: Counter[int] = Counter()
    genre_affinity: Counter[int] = Counter()
    for seed in seeds:
        if seed["id_artista"] is not None:
            artist_affinity[seed["id_artista"]] += seed["weight"]
        if seed["id_genero"] is not None:
            genre_affinity[seed["id_genero"]] += seed["weight"]
    max_artist = max(artist_affinity.values(), default=1.0)
    max_genre = max(genre_affinity.values(), default=1.0)

    ranked: List[Dict[str, Any]] = []
    for item in base:
        track_id = int(item["id_track"])
        if track_id in seed_track_ids:
            continue
        meta = metadata.get(track_id, {})
        features = candidate_features.get(track_id)
        similarity = (
            cosine_similarity(taste_centroid, features.vector)
            if taste_centroid and features
            else 0.0
        )
        artist_match = artist_affinity.get(meta.get("id_artista"), 0.0) / max_artist
        genre_match = genre_affinity.get(meta.get("id_genero"), 0.0) / max_genre
        base_score = float(item.get("score") or 0.0)
        final = base_score * 0.58 + similarity * 0.28 + artist_match * 0.09 + genre_match * 0.05

        reason = "Afinidad con tu actividad en Spotify"
        if artist_match >= 0.5:
            reason = "Artista afín a tus favoritos de Spotify"
        elif genre_match >= 0.5:
            reason = "Género frecuente en tu escucha de Spotify"
        elif similarity >= 0.75:
            reason = "Sonido parecido a lo que escuchas en Spotify"

        ranked.append(
            {
                **item,
                "score": round(final, 4),
                "reason": reason,
                "spotify_track_id": meta.get("spotify_track_id"),
                "spotify_uri": (
                    f"spotify:track:{meta['spotify_track_id']}"
                    if meta.get("spotify_track_id")
                    else None
                ),
                "spotify_similarity": round(similarity, 4),
                "source": "spotify_taste_vox",
            }
        )

    ranked.sort(key=lambda row: row["score"], reverse=True)
    requested_count = len(_unique([*top, *recent, *saved], limit=150))
    return {
        "source": "spotify_taste_vox",
        "coverage": {
            "spotify_signals": requested_count,
            "matched_catalog_tracks": len(seeds),
            "match_percent": round((len(seeds) / requested_count) * 100, 1)
            if requested_count
            else 0.0,
        },
        "tracks": ranked[:limit],
    }
