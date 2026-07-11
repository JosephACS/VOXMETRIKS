from __future__ import annotations

from app.services.scoring._helpers import clamp, min_max_scale


def score_track_engagement(
    *,
    global_engagement: float,
    min_eng: float,
    max_eng: float,
) -> float:
    """Track-level engagement normalized 0–1."""
    return round(min_max_scale(global_engagement, min_eng, max_eng), 4)


def score_user_engagement_signal(
    *,
    total_plays: int,
    total_skips: int,
    total_likes: int,
    warehouse_engagement: float | None,
    max_plays: float = 100.0,
) -> float:
    """
    User activity signal: likes + plays − skips, normalized.
    Used to modulate collaborative confidence, not per-track directly.
    """
    if warehouse_engagement is not None and warehouse_engagement > 0:
        return round(clamp(warehouse_engagement / 10.0), 4)
    raw = total_plays + total_likes * 2 - total_skips
    if raw <= 0:
        return 0.1
    return round(clamp(raw / max(max_plays, 1.0)), 4)


def blend_engagement(
    track_eng: float,
    user_signal: float,
    *,
    skip_penalty: float = 0.0,
) -> float:
    """Combine track engagement with user listening quality (skip rate penalizes)."""
    adjusted = track_eng * (1.0 - clamp(skip_penalty, high=0.5))
    if user_signal > 0:
        adjusted = clamp(0.7 * adjusted + 0.3 * user_signal)
    return round(adjusted, 4)
