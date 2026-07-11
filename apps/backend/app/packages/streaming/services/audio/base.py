"""Audio provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models import ResolvedSource, TrackContext


class AudioProvider(ABC):
    """Common interface for external audio source providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider identifier (e.g. youtube, audius)."""

    @abstractmethod
    def resolve(self, track: TrackContext) -> ResolvedSource:
        """Attempt to resolve a playable source for the track."""

    def validate(self, source_ref: Optional[str], playable_url: Optional[str] = None) -> bool:
        """Lightweight validation before trusting a cached source."""
        return bool(source_ref or playable_url)
