from __future__ import annotations

from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import RecommendationItem, RecommendationsResponse
from app.services.recommendation_engine import RecommendationEngine, UserContext

logger = get_logger(__name__)

DEFAULT_LIMIT = 20


class RecommendationService:
    """Facade over RecommendationEngine — V2 API compatibility."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._engine = RecommendationEngine(client or get_duckdb_client())

    def get_recommendations(self, user_id: int, *, limit: int = DEFAULT_LIMIT) -> RecommendationsResponse:
        ranked = self.rank_tracks(user_id, limit=limit)
        return RecommendationsResponse(
            user_id=user_id,
            recommendations=ranked,
            count=len(ranked),
        )

    def get_for_user(self, user_id: int, *, limit: int = DEFAULT_LIMIT) -> RecommendationsResponse:
        return self.get_recommendations(user_id, limit=limit)

    def rank_tracks(self, user_id: int, *, limit: int = DEFAULT_LIMIT) -> list[RecommendationItem]:
        items = self._engine.recommend(user_id, limit=limit)
        return [
            RecommendationItem(
                track_id=s.track_id,
                track_name=s.track_name,
                artist=s.artist,
                score=s.score,
                reason=s.reason,
                popularity=s.popularity,
                engagement_score=s.engagement_score,
            )
            for s in items
        ]

    def build_user_profile(self, user_id: int) -> UserContext:
        return self._engine.build_user_profile(user_id)
