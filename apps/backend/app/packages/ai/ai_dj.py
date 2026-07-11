"""AI DJ — lightweight listening blocks (text, no voice required)."""

from __future__ import annotations

from typing import Any, Dict, List

from .mood_profile import build_mood_profile


def build_dj_session(
    profile: Dict[str, Any],
    tracks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate 2–3 listening blocks from profile + candidate tracks."""
    audio_dna = profile.get("audio_dna") or {}
    mood = build_mood_profile(audio_dna, {"avg_popularity": _avg_pop(tracks)})
    blocks: List[Dict[str, Any]] = []

    high_energy = [t for t in tracks if (t.get("energy") or 0) >= 0.6][:6]
    chill = [t for t in tracks if (t.get("energy") or 1) <= 0.45][:6]
    favorites_style = tracks[:8]

    if high_energy:
        blocks.append({
            "id": "block-energy",
            "title": "Alta energía",
            "narration": "Ahora siguen canciones con alta energía.",
            "tracks": high_energy,
        })
    if favorites_style and len(blocks) < 3:
        blocks.append({
            "id": "block-taste",
            "title": "Tu estilo",
            "narration": "Esta selección combina tus géneros más escuchados.",
            "tracks": favorites_style,
        })
    if chill:
        blocks.append({
            "id": "block-chill",
            "title": "Ambiente tranquilo",
            "narration": "Después cambiamos a un ambiente más tranquilo.",
            "tracks": chill,
        })

    if not blocks and tracks:
        blocks.append({
            "id": "block-mix",
            "title": "Mix para ti",
            "narration": "Una mezcla basada en tu perfil musical.",
            "tracks": tracks[:10],
        })

    return {
        "mood_profile": mood,
        "blocks": blocks,
        "primary_mood": mood.get("primary_mood"),
    }


def _avg_pop(tracks: List[Dict[str, Any]]) -> float:
    if not tracks:
        return 50.0
    vals = [float(t.get("popularity") or 0) for t in tracks]
    return sum(vals) / len(vals)
