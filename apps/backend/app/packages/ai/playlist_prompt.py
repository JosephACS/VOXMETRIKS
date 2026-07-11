"""Build playlist preview from parsed intent — no auto-save."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

_LABEL_NAMES = {
    "study": "Para estudiar",
    "workout": "Para entrenar",
    "chill": "Para relajarte",
    "melancholy": "Melancólica",
    "happy": "Buen ánimo",
    "instrumental": "Instrumental",
    "acoustic": "Acústica",
    "dance": "Para bailar",
    "popular": "Hits populares",
    "discovery": "Descubrimiento",
    "general": "Playlist personalizada",
}


def build_playlist_from_intent(
    user_prompt: str,
    intent: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    label = intent.get("label", "general")
    name = _LABEL_NAMES.get(label, "Playlist personalizada")
    description = _describe_intent(user_prompt, intent)
    return {
        "name": name,
        "description": description,
        "intent": intent,
        "tracks": [],
        "requires_confirmation": True,
        "provider": intent.get("provider", "local_rules"),
    }


def _describe_intent(prompt: str, intent: Dict[str, Any]) -> str:
    parts: List[str] = []
    label = intent.get("label")
    if label == "study":
        parts.append("Selección tranquila con baja energía para concentrarte.")
    elif label == "workout":
        parts.append("Canciones energéticas y bailables para entrenar.")
    elif label == "chill":
        parts.append("Ambiente relajado para desconectar.")
    elif label == "discovery":
        parts.append("Joyas menos conocidas del catálogo.")
    else:
        parts.append(f"Basada en: {prompt[:120]}")
    if intent.get("genre_query"):
        parts.append(f"Género: {intent['genre_query']}.")
    return " ".join(parts)
