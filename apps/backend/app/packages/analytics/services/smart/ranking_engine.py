"""Hybrid ranking — heuristic engine + content similarity + user signals."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb

from app.services.recommendation_engine import RecommendationEngine

from .feature_extractor import centroid, fetch_track_features, load_user_signal_tracks
from .similarity_engine import cosine_similarity


class RankingEngine:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._heuristic = RecommendationEngine()

    def rank_for_user(
        self,
        app_user_id: int,
        wh_user_id: int,
        *,
        limit: int = 20,
        exclude: Optional[set[int]] = None,
    ) -> List[Dict[str, Any]]:
        exclude = exclude or set()
        heuristic = self._heuristic.recommend(wh_user_id, limit=limit * 2)
        signal_ids = load_user_signal_tracks(self._conn, app_user_id, wh_user_id)
        taste = fetch_track_features(self._conn, signal_ids[:40])
        taste_centroid = centroid([t.vector for t in taste.values()]) if taste else []

        ranked: List[Dict[str, Any]] = []
        for item in heuristic:
            if item.track_id in exclude:
                continue
            content_s = 0.0
            tf = fetch_track_features(self._conn, [item.track_id]).get(item.track_id)
            if tf and taste_centroid:
                content_s = cosine_similarity(taste_centroid, tf.vector)

            fav_boost = 0.15 if item.track_id in signal_ids[:20] else 0.0
            final = item.score * 0.65 + content_s * 0.25 + fav_boost
            ranked.append(
                {
                    "id_track": item.track_id,
                    "nombre_track": item.track_name,
                    "nombre_artista": item.artist,
                    "score": round(final, 4),
                    "reason": item.reason,
                    "content_similarity": round(content_s, 4),
                    "popularity": item.popularity,
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[:limit]
