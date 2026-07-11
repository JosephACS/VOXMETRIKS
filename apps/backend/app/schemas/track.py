from __future__ import annotations

from pydantic import BaseModel, Field


class TopTrackItem(BaseModel):
    id_track: int
    nombre_track: str
    nombre_artista: str
    nombre_genero: str | None = None
    popularity: int = 0
    total_streams: int = 0
    energy: float | None = None
    danceability: float | None = None


class RecommendationItem(BaseModel):
    track_id: int
    score: float
    reason: str
    track_name: str | None = None
    nombre_track: str | None = None
    popularity: int = 0
    engagement_score: float = 0.0


class TrackRecommendationsData(BaseModel):
    user_id: int
    recommendations: list[RecommendationItem] = Field(default_factory=list)
