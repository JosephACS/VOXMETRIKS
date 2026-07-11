"""Extended mood / listener profile labels."""

from __future__ import annotations

from typing import Any, Dict, List

MOOD_LABELS = (
    "Energético", "Acústico", "Bailable", "Tranquilo",
    "Instrumental", "Popular", "Descubridor", "Nostálgico",
)


def classify_mood_from_features(data: Dict[str, Any]) -> str:
    if data.get("energetic") is not None and data.get("energy") is None:
        e = float(data["energetic"]) / 100.0
        d = float(data.get("dance", 0)) / 100.0
        ac = float(data.get("acoustic", 0)) / 100.0
        inst = float(data.get("instrumental", 0)) / 100.0
        pop = float(data.get("popularity") or 50)
    else:
        e = float(data.get("energy") or 0)
        d = float(data.get("danceability") or data.get("dance") or 0)
        ac = float(data.get("acousticness") or data.get("acoustic") or 0)
        inst = float(data.get("instrumentalness") or data.get("instrumental") or 0)
        pop = float(data.get("popularity") or 0)
        if isinstance(data.get("dance"), (int, float)) and data.get("danceability") is None:
            d = float(data["dance"]) / 100.0 if d > 1 else d

    if inst >= 0.5:
        return "Instrumental"
    if e >= 0.65 and d >= 0.55:
        return "Energético"
    if d >= 0.65:
        return "Bailable"
    if ac >= 0.5 and e <= 0.45:
        return "Acústico"
    if e <= 0.35:
        return "Tranquilo"
    if pop >= 70:
        return "Popular"
    if pop <= 35:
        return "Descubridor"
    return "Nostálgico"


def build_mood_profile(
    audio_dna: Dict[str, Any],
    behavior: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Composite mood profile from Audio DNA + listening behavior."""
    behavior = behavior or {}
    primary = classify_mood_from_features(audio_dna)
    scores: Dict[str, int] = {}
    for label in MOOD_LABELS:
        scores[label] = 0

    mapping = {
        "Energético": audio_dna.get("energetic", 0),
        "Acústico": audio_dna.get("acoustic", 0),
        "Bailable": audio_dna.get("dance", 0),
        "Instrumental": audio_dna.get("instrumental", 0),
        "Tranquilo": max(0, 100 - int(audio_dna.get("energetic", 50))),
        "Popular": min(100, int(behavior.get("avg_popularity", 50))),
        "Descubridor": min(100, int(behavior.get("discovery_score", 30))),
        "Nostálgico": audio_dna.get("positive", 40),
    }
    for k, v in mapping.items():
        scores[k] = int(v or 0)

    sorted_traits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {
        "primary_mood": primary,
        "traits": dict(sorted_traits),
        "top_traits": [t[0] for t in sorted_traits[:3]],
    }
