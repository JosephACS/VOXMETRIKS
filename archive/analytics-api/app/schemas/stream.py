from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DailyStreamItem(BaseModel):
    fecha: date
    total_streams: int = 0
    unique_users: int = 0
    unique_tracks: int = 0
    avg_duration_ms: float = 0.0
    skip_count: int = 0


class StreamEngagementItem(BaseModel):
    device_type: str
    stream_count: int = 0
    unique_users: int = 0
    share_pct: float = 0.0
    skip_rate_pct: float | None = None


class DailyStreamsResponse(BaseModel):
    items: list[DailyStreamItem]
    total_days: int
    total_streams: int


class StreamEngagementResponse(BaseModel):
    devices: list[StreamEngagementItem]
    platform_usage: list[dict]
    summary: dict
