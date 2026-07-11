from __future__ import annotations

from app.services.scoring._helpers import clamp, min_max_scale


def score_popularity(
    popularity: int | float,
    *,
    min_pop: float,
    max_pop: float,
    in_top_chart: bool = False,
    playlist_boost: bool = False,
) -> float:
    """Min-max popularity from dim_track / agg_tracks_populares (0–1)."""
    base = min_max_scale(float(popularity), min_pop, max_pop)
    if in_top_chart:
        base = clamp(base + 0.08)
    if playlist_boost:
        base = clamp(base + 0.06)
    return round(base, 4)
