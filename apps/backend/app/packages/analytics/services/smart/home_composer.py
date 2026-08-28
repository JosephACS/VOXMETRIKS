"""Compose personalized Home feed sections."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id
from app.packages.catalog.services.cover_art_service import cover_urls_for_tracks
from app.packages.catalog.services.tracks.playback_availability import playable_track_sql

from .because_you import build_because_sections
from .daily_mix import build_daily_mixes
from .discover_weekly import DISCOVER_WEEKLY_CODE, build_discover_weekly
from .personalization_engine import build_musical_profile
from .ranking_engine import RankingEngine
from .trending_modules import build_trending_modules


def _attach_cover_urls(conn: duckdb.DuckDBPyConnection, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = [int(t["id_track"]) for t in tracks if t.get("id_track") is not None]
    try:
        urls = cover_urls_for_tracks(conn, ids)
    except Exception:
        urls = {}
    out: List[Dict[str, Any]] = []
    for t in tracks:
        item = dict(t)
        tid = item.get("id_track")
        if tid is not None and int(tid) in urls:
            item["cover_url"] = urls[int(tid)]
        out.append(item)
    return out


def _only_playable(
    conn: duckdb.DuckDBPyConnection, tracks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Keep Home rails aligned with the Spotify-backed consumer catalog."""
    ids = [int(t["id_track"]) for t in tracks if t.get("id_track") is not None]
    if not ids:
        return []
    placeholders = ", ".join("?" for _ in ids)
    predicate = playable_track_sql(conn)
    rows = conn.execute(
        f"SELECT dt.id_track FROM dim_track dt "
        f"WHERE dt.id_track IN ({placeholders}) AND ({predicate})",
        ids,
    ).fetchall()
    allowed = {int(row[0]) for row in rows}
    return [t for t in tracks if int(t.get("id_track") or -1) in allowed]


def _enrich_sections(
    conn: duckdb.DuckDBPyConnection, sections: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for section in sections:
        s = dict(section)
        tracks = s.get("tracks") or []
        if isinstance(tracks, list) and tracks:
            s["tracks"] = _attach_cover_urls(conn, _only_playable(conn, tracks))
            if not s["tracks"]:
                continue
        enriched.append(s)
    return enriched


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
                "code": "continue_listening",
                "subtitle_code": "continue_listening_sub",
                "tracks": profile["top_tracks"][:6],
            }
        )

    if recommended:
        sections.append(
            {
                "id": "recommended-for-you",
                "type": "track_rail",
                "code": "recommended_for_you",
                "subtitle_code": "recommended_for_you_sub",
                "tracks": recommended,
            }
        )

    if discover_weekly.get("tracks"):
        sections.append(
            {
                "id": discover_weekly["playlist_id"],
                "type": "playlist",
                "code": discover_weekly.get("code") or DISCOVER_WEEKLY_CODE,
                "week": discover_weekly.get("week"),
                "subtitle_code": "updated_week",
                "tracks": discover_weekly["tracks"],
            }
        )

    for mix in daily_mixes[:3]:
        sections.append(
            {
                "id": mix["playlist_id"],
                "type": "playlist",
                "code": mix["code"],
                "tracks": mix["tracks"],
            }
        )

    sections.extend(because[:2])

    if trending.get("trending_today"):
        sections.append(
            {
                "id": "trending-today",
                "type": "track_rail",
                "code": "trending_today",
                "tracks": trending["trending_today"],
            }
        )

    if profile.get("top_genres"):
        top_g = profile["top_genres"][0]
        genre_name = top_g.get("nombre_genero") or ""
        sections.append(
            {
                "id": f"genre-favorites-{top_g.get('id_genero')}",
                "type": "track_rail",
                "code": "genre_new_releases",
                "subtitle_code": "genre_new_releases_sub",
                "title_params": {"genre": genre_name},
                "tracks": recommended[6:12] if len(recommended) > 6 else recommended,
            }
        )

    sections = _enrich_sections(conn, sections)

    return {
        "user_id": app_user_id,
        "profile": profile,
        "sections": sections,
        "trending": trending,
        "discover_weekly": discover_weekly,
        "daily_mixes": daily_mixes,
    }
