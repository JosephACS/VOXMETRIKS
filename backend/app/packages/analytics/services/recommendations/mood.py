"""Mood-based track selection by energy range."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

MOOD_ENERGY_RANGES: Dict[str, Tuple[float, float]] = {
    "1_muy_baja": (0.0, 0.2),
    "2_baja": (0.2, 0.4),
    "3_media": (0.4, 0.6),
    "4_alta": (0.6, 0.8),
    "5_muy_alta": (0.8, 1.001),
}

MOOD_LABELS: Dict[str, Tuple[str, str]] = {
    "1_muy_baja": ("Chill", "Muy baja energía · ambiente relajado"),
    "2_baja": ("Focus", "Baja energía · concentración moderada"),
    "3_media": ("Balance", "Energía media equilibrada"),
    "4_alta": ("Workout", "Alta energía · actividad física"),
    "5_muy_alta": ("Party", "Máxima intensidad · fiesta"),
}


def parse_energy_range(mood_key: str) -> Optional[Tuple[float, float]]:
    """Convierte id warehouse o rango numérico a (low, high)."""
    if mood_key in MOOD_ENERGY_RANGES:
        return MOOD_ENERGY_RANGES[mood_key]
    normalized = mood_key.replace("_", ".")
    if "-" not in normalized:
        return None
    parts = normalized.split("-", 1)
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def get_mood_tracks(
    conn: duckdb.DuckDBPyConnection,
    mood_key: str,
    limit: int = 12,
) -> List[Dict[str, Any]]:
    parsed = parse_energy_range(mood_key)
    if not parsed:
        return []
    low, high = parsed
    rows = conn.execute(
        """
        SELECT
            dt.id_track,
            dt.nombre_track,
            da.nombre_artista,
            dg.nombre_genero,
            dt.popularity,
            dt.energy,
            ROUND(dt.popularity * 0.6 + dt.energy * 100 * 0.4, 1) AS recommendation_score
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE dt.energy >= ? AND dt.energy < ?
        ORDER BY dt.popularity DESC NULLS LAST
        LIMIT ?
        """,
        [low, high if high < 1.0 else 1.001, limit],
    ).fetchall()
    result = []
    for r in rows:
        artist_raw = r[2] or ""
        primary = artist_raw.split(";")[0].strip() if artist_raw else None
        result.append({
            "id_track": r[0],
            "nombre_track": r[1],
            "nombre_artista": primary,
            "nombre_artista_full": artist_raw,
            "nombre_genero": r[3],
            "popularity": r[4],
            "energy": r[5],
            "recommendation_score": float(r[6] or 0),
        })
    return result
