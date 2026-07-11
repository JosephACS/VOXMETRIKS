from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = Field(description="ok | degraded | error")
    version: str
    environment: str | None = None
    database: str | None = None
    table_count: int = 0
    duckdb_version: str | None = None
    tables: list[str] = Field(default_factory=list)


class ApiResponse(BaseModel):
    status: str = "success"
    data: dict | list | None = None
    message: str = "OK"


class NotImplementedPayload(BaseModel):
    module: str
    message: str = "Endpoint scaffold ready — business logic pending"


# ── Analytics ─────────────────────────────────────────────────────────────────


class DailyStreamsResponse(BaseModel):
    fecha: date | None = None
    total_streams: int
    unique_users: int
    unique_tracks: int
    avg_duration_ms: float
    skip_rate: float = Field(description="Fraction 0–1")


class TopArtistItem(BaseModel):
    id_artista: int
    nombre: str
    streams_7d: int
    growth_pct: float
    total_followers: int | None = None


class TopArtistsResponse(BaseModel):
    items: list[TopArtistItem]
    count: int


class TopTrackItem(BaseModel):
    id_track: int
    track_name: str
    artist: str
    popularity: int
    engagement_score: float
    total_streams: int | None = None


class TopTracksResponse(BaseModel):
    items: list[TopTrackItem]
    count: int


class GenreAnalyticsItem(BaseModel):
    id_genero: int
    genre: str
    popularity: float
    energy_avg: float
    total_tracks: int


class GenresAnalyticsResponse(BaseModel):
    items: list[GenreAnalyticsItem]
    count: int


class PlatformUsageItem(BaseModel):
    platform: str
    device_type: str
    session_count: int
    total_streams: int
    avg_session_min: float
    share_pct: float


class PlatformUsageResponse(BaseModel):
    items: list[PlatformUsageItem]
    count: int


# ── Users ─────────────────────────────────────────────────────────────────────


class UserProfileResponse(BaseModel):
    id_usuario: int
    nombre: str
    email: str | None = None
    pais: str | None = None
    plan: str | None = None
    engagement_score: float
    segment: Literal["power_users", "regular_users", "casual_users", "unknown"]


class UserActivityResponse(BaseModel):
    id_usuario: int
    plays: int
    skips: int
    likes: int
    sessions: int


# ── Streaming ─────────────────────────────────────────────────────────────────


class StreamStartRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    track_id: int = Field(..., ge=1)
    device_type: str = "mobile"
    platform: str = "web"


class StreamStartResponse(BaseModel):
    stream_id: int
    session_id: int
    user_id: int
    track_id: int
    event_type: str = "STREAM_START"
    started_at: datetime
    device_type: str
    platform: str


class StreamEndRequest(BaseModel):
    stream_id: int = Field(..., ge=1)
    duration_ms: int = Field(..., ge=0)
    completed: bool = True
    skipped: bool = False


class StreamEndResponse(BaseModel):
    stream_id: int
    session_id: int | None = None
    event_type: str = "STREAM_END"
    duration_ms: int
    completed: bool
    skipped: bool
    engagement_score: float = 0.0
    ended_at: datetime


class StreamActionRequest(BaseModel):
    stream_id: int = Field(..., ge=1)
    duration_ms: int | None = Field(None, ge=0, description="Elapsed ms at pause/skip")


class StreamActionResponse(BaseModel):
    stream_id: int
    session_id: int | None = None
    event_type: str
    engagement_score: float | None = None
    timestamp: datetime


class LiveSessionStatsResponse(BaseModel):
    user_id: int
    session_id: int | None = None
    active: bool
    session_duration_ms: int
    tracks_played: int
    skip_ratio: float
    current_engagement: float
    device_type: str | None = None
    platform: str | None = None


# ── Search ────────────────────────────────────────────────────────────────────


class SearchTrackHit(BaseModel):
    id_track: int
    track_name: str
    artist: str | None = None


class SearchArtistHit(BaseModel):
    id_artista: int
    artist_name: str


class SearchPlaylistHit(BaseModel):
    id_playlist: int
    playlist_name: str


class SearchResponse(BaseModel):
    query: str
    tracks: list[SearchTrackHit]
    artists: list[SearchArtistHit]
    playlists: list[SearchPlaylistHit]


# ── Recommendations ───────────────────────────────────────────────────────────


class RecommendationItem(BaseModel):
    track_id: int
    track_name: str
    artist: str = ""
    score: float = Field(ge=0, description="Weighted final score 0–1")
    reason: str = Field(description="Human-readable explanation of ranking factors")
    popularity: int | None = None
    engagement_score: float | None = None


class RecommendationsResponse(BaseModel):
    user_id: int
    recommendations: list[RecommendationItem]
    count: int


# ── Dashboard (Angular-ready) ───────────────────────────────────────────────


class EnterpriseHealthResponse(BaseModel):
    status: str = Field(description="ok | degraded | error")
    db: str = Field(description="connected | disconnected")
    etl: str = Field(description="ready | degraded | unknown")
    last_run: date | None = None
    tables: int = 0
    gold_tables: int = 0
    version: str = "2.0.0"


class SystemHealthResponse(BaseModel):
    status: str = Field(description="healthy | degraded | unhealthy")
    db_connected: bool
    tables_ok: bool
    etl_status: str
    gold_ready: bool
    last_pipeline_run: datetime | None = None
    row_counts: dict[str, int] = Field(default_factory=dict)
    version: str = "2.0.0"


class DashboardOverviewResponse(BaseModel):
    total_streams: int
    active_users: int
    total_tracks: int
    top_genre: str
    avg_session_time: float
    skip_rate: float


class LiveTrackItem(BaseModel):
    track_id: int
    track_name: str
    artist: str
    streams: int
    engagement_score: float


class DeviceShareItem(BaseModel):
    platform: str
    device_type: str
    share_pct: float
    total_streams: int


class DashboardRealtimeResponse(BaseModel):
    streams_last_60m: int
    active_users: int
    top_tracks_live: list[LiveTrackItem]
    device_distribution: list[DeviceShareItem]


class GrowthArtistItem(BaseModel):
    id_artista: int
    nombre: str
    streams_7d: int
    growth_pct: float


class DashboardGrowthResponse(BaseModel):
    user_growth_pct: float
    stream_growth_pct: float
    weekly_growth_pct: float
    top_artists: list[GrowthArtistItem] = Field(default_factory=list)


class UserSegmentItem(BaseModel):
    segment: str
    user_count: int
    avg_plays: float
    avg_session_min: float
    retention_pct: float


class DashboardEngagementResponse(BaseModel):
    segments: list[UserSegmentItem]
    power_users_pct: float
    avg_engagement_score: float
    retention_proxy: float
