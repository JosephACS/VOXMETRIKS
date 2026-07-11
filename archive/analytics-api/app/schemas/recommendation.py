from __future__ import annotations

from pydantic import BaseModel


class RecommendationTrackItem(BaseModel):
    id_track: int
    nombre_track: str | None = None
    recommendation_score: float = 0.0
    engagement_score: float = 0.0
    popularity: int = 0


class RecommendationTracksResponse(BaseModel):
    items: list[RecommendationTrackItem]
    total: int
    catalog_coverage_pct: float
