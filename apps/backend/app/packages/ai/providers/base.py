"""AI Provider interface — all AI features go through this layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        ...

    @abstractmethod
    def classify_mood(self, track_or_profile: Dict[str, Any]) -> str:
        ...

    @abstractmethod
    def explain_recommendation(
        self, user_profile: Dict[str, Any], track: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        ...

    @abstractmethod
    def parse_natural_language_search(self, query: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    def generate_playlist_prompt(
        self, user_prompt: str, profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ...

    @property
    def is_external(self) -> bool:
        return False
