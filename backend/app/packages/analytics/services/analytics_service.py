"""Backward-compatible facade for enterprise analytics."""

from .engagement.queries import get_engagement_analytics
from .explorer.security import EXPLORER_BLOCKED_TABLES, SENSITIVE_COLUMN_NAMES
from .explorer.tables import get_table_preview, get_warehouse_tables
from .platform.queries import get_platform_analytics
from .recommendations.mood import MOOD_ENERGY_RANGES, MOOD_LABELS, get_mood_tracks
from .recommendations.service import get_recommendations
from .trending.queries import get_trending_analytics
from .warehouse.status import get_warehouse_status

__all__ = [
    "EXPLORER_BLOCKED_TABLES",
    "MOOD_ENERGY_RANGES",
    "MOOD_LABELS",
    "SENSITIVE_COLUMN_NAMES",
    "get_engagement_analytics",
    "get_mood_tracks",
    "get_platform_analytics",
    "get_recommendations",
    "get_table_preview",
    "get_trending_analytics",
    "get_warehouse_status",
    "get_warehouse_tables",
]
