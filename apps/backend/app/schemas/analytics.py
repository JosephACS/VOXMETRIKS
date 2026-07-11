from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class StreamSeriesPoint(BaseModel):
    fecha: date
    total_streams: int
    unique_users: int
    skip_count: int = 0
    avg_duration_ms: float = 0.0


class PeakHourItem(BaseModel):
    hour_of_day: int
    stream_count: int


class StreamsAnalyticsData(BaseModel):
    start_date: date
    end_date: date
    series: list[StreamSeriesPoint] = Field(default_factory=list)
    peak_hours: list[PeakHourItem] = Field(default_factory=list)
    trending_artists: list[dict] = Field(default_factory=list)
    top_genres: list[dict] = Field(default_factory=list)
    device_breakdown: list[dict] = Field(default_factory=list)
