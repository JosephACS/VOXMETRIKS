"""AI provider factory — external optional, local always available."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings

from .providers.base import AIProvider
from .providers.external import ExternalLLMProvider
from .providers.local import LocalRuleBasedAIProvider
from .providers.mock import MockAIProvider


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    mode = settings.ai_provider.strip().lower()
    if mode == "mock":
        return MockAIProvider()
    if mode == "external":
        ext = ExternalLLMProvider()
        if ext.is_external:
            return ext
    return LocalRuleBasedAIProvider()


def get_ai_provider_status() -> dict:
    provider = get_ai_provider()
    return {
        "active": provider.name,
        "external_available": isinstance(provider, ExternalLLMProvider) and provider.is_external,
        "fallback": "local_rules",
    }
