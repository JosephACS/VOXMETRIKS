from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class GenreTrendItem(BaseModel):
    id_genero: int
    nombre_genero: str
    streams_7d: int = 0
    trend_pct: float = 0.0


class DeviceUsageItem(BaseModel):
    platform: str
    device_type: str
    total_streams: int = 0
    share_pct: float = 0.0


class GrowthTrendPoint(BaseModel):
    fecha: date
    total_streams: int
    unique_users: int


class DashboardOverviewData(BaseModel):
    total_streams: int = 0
    active_users: int = 0
    top_genres: list[GenreTrendItem] = Field(default_factory=list)
    top_artists: list[dict] = Field(default_factory=list)
    device_usage: list[DeviceUsageItem] = Field(default_factory=list)
    growth_trends: list[GrowthTrendPoint] = Field(default_factory=list)
