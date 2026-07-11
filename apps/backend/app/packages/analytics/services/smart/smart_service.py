"""Smart Recommendation Engine — public facade."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.core.cache import cache_get, cache_set, make_cache_key, ttl_for

from .because_you import build_because_sections
from .daily_mix import build_daily_mixes
from .discover_weekly import build_discover_weekly
from .home_composer import compose_home
from .personalization_engine import build_musical_profile
from .ranking_engine import RankingEngine
from .similarity_engine import similar_artists, similar_tracks
from .trending_modules import build_trending_modules
from app.packages.analytics.services.history_service import _warehouse_user_id


class SmartRecommendationService:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_home(self, user_id: int) -> Dict[str, Any]:
        key = make_cache_key("smart:home", user_id)
        hit = cache_get(key)
        if hit is not None:
            return hit
        home = compose_home(self._conn, user_id)
        try:
            from app.packages.ai.service import AIService
            widgets = AIService(self._conn).intent_widgets(user_id)
            if widgets:
                home["sections"] = widgets + home.get("sections", [])
        except Exception:
            pass
        cache_set(key, home, ttl_for("smart_home"))
        return home

    def get_profile(self, user_id: int) -> Dict[str, Any]:
        return build_musical_profile(self._conn, user_id)

    def get_discover_weekly(self, user_id: int, *, limit: int = 30) -> Dict[str, Any]:
        return build_discover_weekly(self._conn, user_id, limit=limit)

    def get_daily_mixes(self, user_id: int) -> List[Dict[str, Any]]:
        return build_daily_mixes(self._conn, user_id)

    def get_because_you(self, user_id: int) -> List[Dict[str, Any]]:
        return build_because_sections(self._conn, user_id)

    def get_recommendations(self, user_id: int, *, limit: int = 20) -> List[Dict[str, Any]]:
        wh = _warehouse_user_id(user_id)
        return RankingEngine(self._conn).rank_for_user(user_id, wh, limit=limit)

    def get_similar_tracks(self, track_id: int, *, limit: int = 12) -> List[Dict[str, Any]]:
        return similar_tracks(self._conn, track_id, limit=limit)

    def get_similar_artists(self, artist_id: int, *, limit: int = 8) -> List[Dict[str, Any]]:
        return similar_artists(self._conn, artist_id, limit=limit)

    def get_trending(self) -> Dict[str, Any]:
        return build_trending_modules(self._conn)
