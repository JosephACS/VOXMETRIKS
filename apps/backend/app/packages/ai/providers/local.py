"""Rule-based AI — works offline, no API keys required."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import AIProvider
from ..nl_search import parse_nl_query
from ..explain import explain_from_reason
from ..mood_profile import classify_mood_from_features
from ..playlist_prompt import build_playlist_from_intent


class LocalRuleBasedAIProvider(AIProvider):
    name = "local_rules"

    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        ctx = context or {}
        if ctx.get("task") == "playlist_description":
            return ctx.get("description") or "Playlist generada según tu intención musical."
        return "Respuesta generada localmente."

    def classify_mood(self, track_or_profile: Dict[str, Any]) -> str:
        return classify_mood_from_features(track_or_profile)

    def explain_recommendation(
        self, user_profile: Dict[str, Any], track: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        reason = track.get("reason") or (context or {}).get("reason")
        return explain_from_reason(reason, track, user_profile)

    def parse_natural_language_search(self, query: str) -> Dict[str, Any]:
        return parse_nl_query(query)

    def generate_playlist_prompt(
        self, user_prompt: str, profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        intent = parse_nl_query(user_prompt)
        return build_playlist_from_intent(user_prompt, intent, profile)
