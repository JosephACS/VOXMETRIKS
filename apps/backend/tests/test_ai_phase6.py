"""Tests for VOXMETRIKS AI — Phase 6."""

import os

from app.packages.ai.factory import get_ai_provider, get_ai_provider_status
from app.packages.ai.nl_search import parse_nl_query
from app.packages.ai.explain import explain_from_reason
from app.packages.ai.mood_profile import classify_mood_from_features, build_mood_profile
from app.packages.ai.sanitizer import sanitize_ai_context
from app.packages.ai.providers.mock import MockAIProvider


def test_local_provider_without_api_key():
    os.environ["AI_PROVIDER"] = "local"
    get_ai_provider.cache_clear()
    status = get_ai_provider_status()
    assert status["active"] in ("local_rules", "mock")
    assert status["fallback"] == "local_rules"


def test_nl_search_study_intent():
    intent = parse_nl_query("música tranquila para estudiar")
    assert intent.get("label") == "study"
    assert intent.get("energy_max", 1) <= 0.5


def test_nl_search_workout_intent():
    intent = parse_nl_query("canciones energéticas para entrenar")
    assert intent.get("label") == "workout"
    assert intent.get("energy_min", 0) >= 0.6


def test_explain_from_reason_code():
    text = explain_from_reason("high_popularity", {"id_track": 1}, {})
    assert "popular" in text.lower()


def test_mood_profile_from_audio_dna():
    mood = build_mood_profile({"energetic": 85, "dance": 70, "acoustic": 10, "instrumental": 5, "positive": 60})
    assert mood["primary_mood"]
    assert len(mood["top_traits"]) >= 1


def test_sanitizer_strips_secrets():
    clean = sanitize_ai_context({"token": "secret", "username": "demo_user", "track": {"id": 1}})
    assert "token" not in clean
    assert clean["username"].endswith("***")


def test_mock_provider_explain():
    p = MockAIProvider()
    text = p.explain_recommendation({}, {"id_track": 1})
    assert "Mock" in text


def test_playlist_preview_requires_confirmation():
    p = MockAIProvider()
    out = p.generate_playlist_prompt("playlist para entrenar", {})
    assert out.get("requires_confirmation") is True
