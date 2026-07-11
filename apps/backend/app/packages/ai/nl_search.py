"""Natural language query → audio feature filters (local rules)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Intent patterns (Spanish + English)
_INTENTS: List[tuple[tuple[str, ...], Dict[str, Any]]] = [
    (("estudiar", "study", "concentr", "focus", "programar", "coding", "trabajo"), {
        "energy_max": 0.45, "acousticness_min": 0.35, "speechiness_max": 0.25, "label": "study",
    }),
    (("entrenar", "workout", "gym", "correr", "run", "energ", "fiesta", "party"), {
        "energy_min": 0.65, "danceability_min": 0.55, "label": "workout",
    }),
    (("tranquil", "calm", "chill", "relax", "dormir", "sleep", "noche"), {
        "energy_max": 0.4, "valence_max": 0.55, "acousticness_min": 0.25, "label": "chill",
    }),
    (("triste", "sad", "melanc", "llorar"), {
        "valence_max": 0.35, "energy_max": 0.5, "label": "melancholy",
    }),
    (("feliz", "happy", "alegre", "positiv"), {
        "valence_min": 0.6, "energy_min": 0.45, "label": "happy",
    }),
    (("instrumental", "sin voz", "sin letra"), {
        "instrumentalness_min": 0.5, "speechiness_max": 0.1, "label": "instrumental",
    }),
    (("acust", "acoustic", "unplugged"), {
        "acousticness_min": 0.55, "label": "acoustic",
    }),
    (("bailar", "dance", "disco", "reggaeton"), {
        "danceability_min": 0.65, "energy_min": 0.5, "label": "dance",
    }),
    (("popular", "hits", "top", "chart"), {
        "popularity_min": 60, "label": "popular",
    }),
    (("descubrir", "nuevo", "underground", "indie", "poco conocid"), {
        "popularity_max": 45, "label": "discovery",
    }),
]

_GENRE_HINTS = {
    "rock": "rock", "pop": "pop", "jazz": "jazz", "metal": "metal",
    "hip hop": "hip hop", "rap": "rap", "reggae": "reggae", "clásica": "classical",
    "classical": "classical", "electronic": "electronic", "edm": "electronic",
    "latin": "latin", "salsa": "latin", "country": "country", "blues": "blues",
}


def parse_nl_query(query: str) -> Dict[str, Any]:
    q = (query or "").strip().lower()
    if not q:
        return {"keywords": [], "label": "empty"}

    result: Dict[str, Any] = {"keywords": [], "original": query.strip(), "label": "general"}
    matched_label: Optional[str] = None

    for patterns, filters in _INTENTS:
        if any(p in q for p in patterns):
            result.update(filters)
            matched_label = filters.get("label")
            break

    for hint, genre in _GENRE_HINTS.items():
        if hint in q:
            result["genre_query"] = genre
            break

    # "parecido a X" / "like X" → artist hint
    artist_match = re.search(r"(?:parecido a|similar a|like|como)\s+(.+?)(?:\s+para|\s+con|$)", q)
    if artist_match:
        result["artist_query"] = artist_match.group(1).strip()

    # tempo hints
    if "lento" in q or "slow" in q:
        result["tempo_max"] = 100
    if "rápid" in q or "fast" in q:
        result["tempo_min"] = 130

    # remaining tokens for keyword search
    stop = {"música", "musica", "canciones", "songs", "algo", "quiero", "para", "de", "con", "la", "el", "un", "una"}
    tokens = [t for t in re.split(r"\W+", q) if t and t not in stop and len(t) > 2]
    result["keywords"] = tokens[:8]
    if matched_label:
        result["label"] = matched_label
    result["provider"] = "local_rules"
    return result
