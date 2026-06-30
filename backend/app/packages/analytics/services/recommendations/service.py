"""Personalized recommendations from warehouse aggregates."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import duckdb

from app.core.query_helpers import fetch_rows
from app.packages.streaming.services.display_text import sanitize_display_text

from ..stats.catalog import get_top_tracks_by_popularity
from .mood import MOOD_LABELS, get_mood_tracks

logger = logging.getLogger(__name__)


def _clean_track_labels(track: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(track)
    if "nombre_track" in cleaned:
        cleaned["nombre_track"] = sanitize_display_text(cleaned.get("nombre_track"))
    if "nombre_artista" in cleaned:
        cleaned["nombre_artista"] = sanitize_display_text(cleaned.get("nombre_artista"))
    return cleaned


def get_recommendations(
    conn: duckdb.DuckDBPyConnection,
    favorite_genre: Optional[str] = None,
    limit: int = 12,
    mood: Optional[str] = None,
) -> Dict[str, Any]:
    tracks: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_recommendation_scores",
            columns=[
                "id_track", "nombre_track", "nombre_artista", "nombre_genero",
                "recommendation_score", "engagement_score", "popularity",
            ],
            order_by="recommendation_score DESC",
            limit=limit,
        )
        tracks = rows
    except Exception:
        logger.exception("get_recommendations: agg_recommendation_scores unavailable; using popularity fallback")
        raw = get_top_tracks_by_popularity(conn, limit=limit)
        tracks = [
            {
                "id_track": t.get("id_track"),
                "nombre_track": t.get("nombre_track"),
                "nombre_artista": t.get("nombre_artista"),
                "nombre_genero": t.get("nombre_genero"),
                "recommendation_score": t.get("popularity"),
                "popularity": t.get("popularity"),
            }
            for t in raw
        ]

    if favorite_genre and tracks:
        genre_lower = favorite_genre.lower()
        preferred = [t for t in tracks if (t.get("nombre_genero") or "").lower() == genre_lower]
        others = [t for t in tracks if (t.get("nombre_genero") or "").lower() != genre_lower]
        tracks = preferred + others

    artists: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_top_artistas",
            columns=["id_artista", "nombre_artista", "promedio_popularidad", "total_tracks"],
            order_by="promedio_popularidad DESC",
            limit=8,
        )
        artists = [
            {
                **r,
                "affinity": round((r.get("promedio_popularidad") or 0), 1),
            }
            for r in rows
        ]
    except Exception:
        logger.exception("get_recommendations: agg_top_artistas unavailable")

    genres: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_genero_popularidad",
            columns=["id_genero", "nombre_genero", "popularidad_promedio", "total_tracks"],
            order_by="popularidad_promedio DESC",
            limit=10,
        )
        max_pop = max((r.get("popularidad_promedio") or 0) for r in rows) if rows else 1
        genres = [
            {
                "genre": r.get("nombre_genero"),
                "score": round(((r.get("popularidad_promedio") or 0) / max_pop) * 100, 1),
                "total_tracks": r.get("total_tracks"),
            }
            for r in rows
        ]
    except Exception:
        logger.exception("get_recommendations: agg_genero_popularidad unavailable")

    moods: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_distribucion_energia",
            columns=["rango_energia", "cantidad_tracks", "popularidad_promedio"],
            order_by="rango_energia",
        )
        for r in rows:
            key = r.get("rango_energia", "")
            meta = MOOD_LABELS.get(key, (key.replace("_", " ").title(), "Colección por energía"))
            moods.append({
                "id": key,
                "name": meta[0],
                "description": meta[1],
                "tracks": int(r.get("cantidad_tracks") or 0),
            })
    except Exception:
        logger.exception("get_recommendations: agg_distribucion_energia unavailable")

    mood_tracks: List[Dict[str, Any]] = []
    mood_label = None
    if mood:
        mood_tracks = get_mood_tracks(conn, mood, limit=limit)
        for m in moods:
            if m.get("id") == mood:
                mood_label = m.get("name")
                break
        if not mood_label:
            meta = MOOD_LABELS.get(mood)
            mood_label = meta[0] if meta else mood.replace("_", " ")

    return {
        "for_you": [_clean_track_labels(t) for t in tracks],
        "artists": artists,
        "genres": genres,
        "moods": moods,
        "mood_filter": mood,
        "mood_label": mood_label,
        "mood_tracks": [_clean_track_labels(t) for t in mood_tracks],
        "mood_count": len(mood_tracks),
    }
