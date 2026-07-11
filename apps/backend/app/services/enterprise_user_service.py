from __future__ import annotations

from app.core.logging import get_logger
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserInsightsData

logger = get_logger(__name__)


class EnterpriseUserService:
    """User insights from GOLD + fact tables."""

    def __init__(self, repo: UserRepository | None = None) -> None:
        self._repo = repo or UserRepository()

    def get_user_insights(self, user_id: int) -> UserInsightsData | None:
        if not self._repo.user_exists(user_id):
            return None

        activity = self._repo.get_user_activity(user_id) or {}
        favorites = self._repo.get_favorites_count(user_id)

        return UserInsightsData(
            user_id=user_id,
            engagement_score=float(activity.get("engagement_score") or 0),
            total_plays=int(activity.get("total_plays") or 0),
            skips=int(activity.get("total_skips") or 0),
            favorites=favorites or int(activity.get("total_likes") or 0),
            segment=self._repo.get_engagement_segment(user_id),
        )
