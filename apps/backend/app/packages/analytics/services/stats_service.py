"""Backward-compatible facade for stats queries and synthetic generation."""

from .stats.catalog import (
    get_catalog_growth,
    get_energia_distribution,
    get_last_loads,
    get_top_tracks_by_popularity,
)
from .stats.constants import (
    ACTIVITY_FACT_TABLES,
    MAX_CREATE_PER_RUN,
    MAX_TARGET_TOTAL,
    SYNTHETIC_BATCH_SIZE,
    WARN_CREATE_ABOVE,
)
from .stats.summary import get_summary
from .stats.events_inventory import get_events_breakdown
from .synthetic.generator import (
    generate_synthetic_activity,
    generate_synthetic_tracks,
    get_synthetic_limits,
)

__all__ = [
    "ACTIVITY_FACT_TABLES",
    "MAX_CREATE_PER_RUN",
    "MAX_TARGET_TOTAL",
    "SYNTHETIC_BATCH_SIZE",
    "WARN_CREATE_ABOVE",
    "generate_synthetic_activity",
    "generate_synthetic_tracks",
    "get_catalog_growth",
    "get_energia_distribution",
    "get_events_breakdown",
    "get_last_loads",
    "get_summary",
    "get_synthetic_limits",
    "get_top_tracks_by_popularity",
]
