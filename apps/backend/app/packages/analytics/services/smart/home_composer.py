"""Compose personalized Home feed sections."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id

from .because_you import build_because_sections
from .daily_mix import build_daily_mixes
from .discover_weekly import build_discover_weekly
from .personalization_engine import build_musical_profile
from .ranking_engine import RankingEngine
from .trending_modules import build_trending_modules


def compose_home(
    conn: duckdb.DuckDBPyConnection, app_user_id: int
) -> Dict[str, Any]:
    wh_user = _warehouse_user_id(app_user_id)
    profile = build_musical_profile(conn, app_user_id)
    ranker = RankingEngine(conn)
    recommended = ranker.rank_for_user(app_user_id, wh_user, limit=12)
    discover_weekly = build_discover_weekly(conn, app_user_id, limit=25)
    daily_mixes = build_daily_mixes(conn, app_user_id, limit=15)
    because = build_because_sections(conn, app_user_id, limit=8)
    trending = build_trending_modules(conn, limit=10)

    sections: List[Dict[str, Any]] = []

    if profile.get("top_tracks"):
        sections.append(
            {
                "id": "continue-listening",
                "type": "track_rail",
                "title": "Seguir escuchando",
                "subtitle": "Basado en tu actividad reciente",
                "tracks": profile["top_tracks"][:6],
            }
        )

    if recommended:
        sections.append(
            {
                "id": "recommended-for-you",
                "type": "track_rail",
                "title": "Recomendado para ti",
                "subtitle": "Personalizado con tus gustos",
                "tracks": recommended,
            }
        )

    if discover_weekly.get("tracks"):
        sections.append(
            {
                "id": discover_weekly["playlist_id"],
                "type": "playlist",
                "title": discover_weekly["title"],
                "subtitle": f"Actualizado {discover_weekly.get('week', '')}",
                "tracks": discover_weekly["tracks"],
            }
        )

    for mix in daily_mixes[:3]:
        sections.append(
            {
                "id": mix["playlist_id"],
                "type": "playlist",
                "title": mix["title"],
                "tracks": mix["tracks"],
            }
        )

    sections.extend(because[:2])

    if trending.get("trending_today"):
        sections.append(
            {
                "id": "trending-today",
                "type": "track_rail",
                "title": "Trending Today",
                "tracks": trending["trending_today"],
            }
        )

    if profile.get("top_genres"):
        top_g = profile["top_genres"][0]
        sections.append(
            {
                "id": f"genre-favorites-{top_g.get('id_genero')}",
                "type": "track_rail",
                "title": f"Nuevos lanzamientos de {top_g.get('nombre_genero', 'tu género')}",
                "subtitle": "Del género que más escuchas",
                "tracks": recommended[6:12] if len(recommended) > 6 else recommended,
            }
        )

    return {
        "user_id": app_user_id,
        "profile": profile,
        "sections": sections,
        "trending": trending,
        "discover_weekly": discover_weekly,
        "daily_mixes": daily_mixes,
    }
