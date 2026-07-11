"""Deterministic AI provider for tests."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .local import LocalRuleBasedAIProvider


class MockAIProvider(LocalRuleBasedAIProvider):
    name = "mock"

    def explain_recommendation(
        self, user_profile: Dict[str, Any], track: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        return "Mock: recomendada por prueba."

    def generate_playlist_prompt(
        self, user_prompt: str, profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        base = super().generate_playlist_prompt(user_prompt, profile)
        base["name"] = "Mock Playlist"
        base["provider"] = "mock"
        return base
