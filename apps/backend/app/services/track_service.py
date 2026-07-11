from __future__ import annotations

from app.core.cache import cache_get, cache_set, make_cache_key, ttl_for
from app.core.logging import get_logger
from app.repositories.track_repository import TrackRepository
from app.schemas.track import RecommendationItem, TopTrackItem
from app.services.recommendation_engine import RecommendationEngine

logger = get_logger(__name__)


class TrackService:
    """Track catalog analytics — top charts and statistical recommendations."""

    def __init__(
        self,
        repo: TrackRepository | None = None,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self._repo = repo or TrackRepository()
        self._engine = engine or RecommendationEngine()

    def get_top_tracks(self, *, limit: int = 20) -> list[TopTrackItem]:
        cache_key = make_cache_key("enterprise.tracks.top", limit)
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        rows = self._repo.get_top_tracks(limit=limit)
        result = [
            TopTrackItem(
                id_track=int(r["id_track"]),
                nombre_track=str(r.get("nombre_track") or ""),
                nombre_artista=str(r.get("nombre_artista") or ""),
                nombre_genero=r.get("nombre_genero"),
                popularity=int(r.get("popularity") or 0),
                total_streams=int(r.get("total_streams") or 0),
                energy=float(r["energy"]) if r.get("energy") is not None else None,
                danceability=float(r["danceability"]) if r.get("danceability") is not None else None,
            )
            for r in rows
        ]
        if result:
            cache_set(cache_key, result, ttl_for("top_tracks"))
        return result

    def get_recommendations(self, user_id: int, *, limit: int = 20) -> list[RecommendationItem]:
        scored = self._engine.recommend(user_id, limit=limit)
        return [
            RecommendationItem(
                track_id=s.track_id,
                score=s.score,
                reason=s.reason,
                track_name=s.track_name,
                popularity=s.popularity,
                engagement_score=s.engagement_score,
            )
            for s in scored
        ]
