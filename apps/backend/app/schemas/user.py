from __future__ import annotations

from pydantic import BaseModel


class UserInsightsData(BaseModel):
    user_id: int
    engagement_score: float = 0.0
    total_plays: int = 0
    skips: int = 0
    favorites: int = 0
    segment: str | None = None
