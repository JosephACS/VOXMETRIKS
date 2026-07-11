from __future__ import annotations

from pydantic import BaseModel


class UserSegmentItem(BaseModel):
    segment: str
    user_count: int = 0
    avg_plays: float = 0.0
    avg_session_min: float = 0.0
    retention_pct: float = 0.0


class UserRetentionItem(BaseModel):
    cohort_week: str
    users_cohort: int = 0
    week_1_pct: float = 0.0
    week_2_pct: float = 0.0
    week_4_pct: float = 0.0


class UserSegmentsResponse(BaseModel):
    segments: list[UserSegmentItem]
    total_users: int


class UserRetentionResponse(BaseModel):
    cohorts: list[UserRetentionItem]
    total_cohorts: int
