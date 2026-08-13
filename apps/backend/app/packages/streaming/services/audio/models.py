"""Data models for multi-provider audio resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TrackContext:
    """Catalog metadata used to search external audio providers."""

    track_id: int
    track_name: str
    artist_name: str
    duration_ms: Optional[int] = None
    album_name: Optional[str] = None
    # Video/source refs already known to fail at playback (try next candidate).
    exclude_source_refs: frozenset[str] = field(default_factory=frozenset)


@dataclass
class ResolvedSource:
    """Result of a provider resolve attempt."""

    track_id: int
    provider: str
    status: str
    source_ref: Optional[str] = None
    youtube_video_id: Optional[str] = None
    playable_url: Optional[str] = None
    query: Optional[str] = None
    confidence_score: Optional[float] = None

    def to_api_dict(self) -> dict:
        """Serialize for API response (backward compatible)."""
        yt_id = self.youtube_video_id
        if self.provider == "youtube" and self.source_ref and not yt_id:
            yt_id = self.source_ref
        return {
            "track_id": self.track_id,
            "provider": self.provider,
            "youtube_video_id": yt_id,
            "source_ref": self.source_ref,
            "playable_url": self.playable_url,
            "query": self.query,
            "status": self.status,
            "confidence_score": self.confidence_score,
        }


@dataclass
class ResolutionLog:
    """Internal observability record (not exposed to clients)."""

    track_id: int
    provider: str
    outcome: str
    elapsed_ms: float
    from_cache: bool = False
    fallback: bool = False
    error: Optional[str] = field(default=None)
