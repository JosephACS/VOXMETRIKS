"""Optional external LLM — OpenAI-compatible API, disabled without API key."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

from ..sanitizer import sanitize_ai_context
from .local import LocalRuleBasedAIProvider

logger = get_logger("voxmetrik.ai.external")


class ExternalLLMProvider(LocalRuleBasedAIProvider):
    """Falls back to local rules on any failure or missing key."""

    name = "external_llm"

    def __init__(self) -> None:
        self._fallback = LocalRuleBasedAIProvider()
        settings = get_settings()
        self._api_key = settings.ai_llm_api_key.strip()
        self._base_url = settings.ai_llm_base_url.rstrip("/")
        self._model = settings.ai_llm_model

    @property
    def is_external(self) -> bool:
        return bool(self._api_key)

    def _chat(self, system: str, user: str, *, max_tokens: int = 256) -> Optional[str]:
        if not self._api_key:
            return None
        try:
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.4,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning("llm_call_failed error=%s", str(exc)[:200])
            return None

    def explain_recommendation(
        self, user_profile: Dict[str, Any], track: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        safe = sanitize_ai_context({"profile": user_profile, "track": track, "context": context})
        prompt = (
            "Explica en una frase corta (español) por qué se recomienda esta canción. "
            f"Datos: {json.dumps(safe, ensure_ascii=False)[:800]}"
        )
        out = self._chat("Eres un asistente musical conciso.", prompt, max_tokens=80)
        return out or self._fallback.explain_recommendation(user_profile, track, context)

    def generate_playlist_prompt(
        self, user_prompt: str, profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        base = self._fallback.generate_playlist_prompt(user_prompt, profile)
        safe = sanitize_ai_context({"prompt": user_prompt, "profile": profile})
        name = self._chat(
            "Genera solo un título corto de playlist en español.",
            f"Intención: {user_prompt}\nPerfil: {json.dumps(safe.get('profile', {}), ensure_ascii=False)[:400]}",
            max_tokens=24,
        )
        if name:
            base["name"] = name.strip('" ')
        desc = self._chat(
            "Genera una descripción de playlist en una frase (español).",
            user_prompt,
            max_tokens=60,
        )
        if desc:
            base["description"] = desc
        base["provider"] = self.name if self.is_external else "local_rules"
        return base

    def parse_natural_language_search(self, query: str) -> Dict[str, Any]:
        return self._fallback.parse_natural_language_search(query)
