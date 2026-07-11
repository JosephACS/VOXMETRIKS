"""Human-readable recommendation explanations from reason codes."""

from __future__ import annotations

from typing import Any, Dict, Optional

_REASON_TEXT = {
    "high_popularity": "Es popular dentro del catálogo y encaja con tendencias actuales.",
    "catalog_discovery": "Te ayuda a descubrir joyas menos obvias del catálogo.",
    "genre_affinity": "Coincide con géneros que escuchas con frecuencia.",
    "artist_affinity": "De un artista similar a los que ya disfrutas.",
    "mood_match": "Encaja con el estado de ánimo que buscas.",
    "collaborative": "Usuarios con gustos parecidos también la escuchan.",
    "trending_boost": "Está en tendencia esta semana.",
    "favorite_boost": "Relacionada con tus favoritos.",
    "content_similar": "Tiene características de audio similares a tus favoritos.",
    "energy_match": "Coincide con tu preferencia por canciones energéticas.",
    "acoustic_match": "Encaja con tu perfil más acústico.",
}


def explain_from_reason(
    reason: Optional[str],
    track: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> str:
    if reason and reason in _REASON_TEXT:
        return _REASON_TEXT[reason]

    if track.get("similarity"):
        return "Tiene características de audio similares a lo que escuchas."
    if track.get("content_similarity"):
        return "Coincide con tu perfil sonoro (Audio DNA)."
    if profile and profile.get("top_genres"):
        return "Es popular dentro de tus géneros frecuentes."
    return "Recomendada porque encaja con tu actividad reciente."
