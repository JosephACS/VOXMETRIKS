"""VOXMETRIKS AI facade — orchestrates provider + warehouse queries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb

from app.core.cache import cache_get, cache_set, make_cache_key, ttl_for
from app.packages.ai.ai_dj import build_dj_session
from app.packages.ai.factory import get_ai_provider
from app.packages.ai.mood_profile import build_mood_profile
from app.packages.analytics.services.smart.personalization_engine import build_musical_profile
from app.packages.analytics.services.smart.ranking_engine import RankingEngine
from app.packages.analytics.services.history_service import _warehouse_user_id

from ._helpers import table_exists_conn


class AIService:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._provider = get_ai_provider()

    def provider_status(self) -> Dict[str, Any]:
        from app.packages.ai.factory import get_ai_provider_status
        return get_ai_provider_status()

    def parse_search(self, query: str) -> Dict[str, Any]:
        return self._provider.parse_natural_language_search(query)

    def search_tracks(self, query: str, *, limit: int = 24) -> Dict[str, Any]:
        intent = self.parse_search(query)
        tracks = self._query_tracks(intent, limit=limit)
        return {"query": query, "intent": intent, "tracks": tracks, "total": len(tracks)}

    def preview_playlist(self, user_id: int, prompt: str, *, limit: int = 20) -> Dict[str, Any]:
        profile = build_musical_profile(self._conn, user_id)
        preview = self._provider.generate_playlist_prompt(prompt, profile)
        intent = preview.get("intent") or self.parse_search(prompt)
        tracks = self._query_tracks(intent, limit=limit, user_id=user_id)
        preview["tracks"] = tracks
        preview["track_count"] = len(tracks)
        preview["requires_confirmation"] = True
        return preview

    def explain_track(self, user_id: int, track_id: int) -> Dict[str, Any]:
        profile = build_musical_profile(self._conn, user_id)
        wh = _warehouse_user_id(user_id)
        ranked = RankingEngine(self._conn).rank_for_user(user_id, wh, limit=50)
        track = next((t for t in ranked if int(t.get("id_track", 0)) == track_id), None)
        if not track:
            track = self._fetch_track(track_id)
        if not track:
            return {"track_id": track_id, "explanation": "No hay datos suficientes para explicar esta recomendación."}
        text = self._provider.explain_recommendation(profile, track)
        return {"track_id": track_id, "explanation": text, "reason": track.get("reason")}

    def mood_profile(self, user_id: int) -> Dict[str, Any]:
        key = make_cache_key("ai:mood", user_id)
        hit = cache_get(key)
        if hit:
            return hit
        profile = build_musical_profile(self._conn, user_id)
        mood = build_mood_profile(profile.get("audio_dna") or {}, {
            "avg_popularity": _avg_from_top(profile.get("top_tracks") or []),
            "discovery_score": min(100, len(profile.get("top_genres") or []) * 15),
        })
        result = {"user_id": user_id, "audio_dna": profile.get("audio_dna"), "mood": mood}
        cache_set(key, result, ttl_for("smart_home"))
        return result

    def dj_session(self, user_id: int, *, limit: int = 30) -> Dict[str, Any]:
        profile = build_musical_profile(self._conn, user_id)
        wh = _warehouse_user_id(user_id)
        tracks = RankingEngine(self._conn).rank_for_user(user_id, wh, limit=limit)
        enriched = [self._enrich_track(t) for t in tracks]
        session = build_dj_session(profile, enriched)
        session["user_id"] = user_id
        return session

    def intent_widgets(self, user_id: int) -> List[Dict[str, Any]]:
        """Smart home intent widgets — study, workout, relax."""
        widgets = []
        for label, title, subtitle in (
            ("study", "Para estudiar", "Concentración y calma"),
            ("workout", "Para entrenar", "Alta energía"),
            ("chill", "Para relajarte", "Ambiente tranquilo"),
        ):
            intent = self.parse_search(title)
            tracks = self._query_tracks(intent, limit=8, user_id=user_id)
            if tracks:
                widgets.append({
                    "id": f"ai-intent-{label}",
                    "type": "track_rail",
                    "title": title,
                    "subtitle": subtitle,
                    "tracks": tracks,
                })
        return widgets

    def _query_tracks(
        self, intent: Dict[str, Any], *, limit: int = 24, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if not table_exists_conn(self._conn, "dim_track"):
            return []
        wh = []
        params: List[Any] = []

        def _add(col: str, op: str, val: Any) -> None:
            wh.append(f"dt.{col} {op} ?")
            params.append(val)

        if intent.get("energy_min") is not None:
            _add("energy", ">=", intent["energy_min"])
        if intent.get("energy_max") is not None:
            _add("energy", "<=", intent["energy_max"])
        if intent.get("danceability_min") is not None:
            _add("danceability", ">=", intent["danceability_min"])
        if intent.get("valence_min") is not None:
            _add("valence", ">=", intent["valence_min"])
        if intent.get("valence_max") is not None:
            _add("valence", "<=", intent["valence_max"])
        if intent.get("acousticness_min") is not None:
            _add("acousticness", ">=", intent["acousticness_min"])
        if intent.get("instrumentalness_min") is not None:
            _add("instrumentalness", ">=", intent["instrumentalness_min"])
        if intent.get("speechiness_max") is not None:
            _add("speechiness", "<=", intent["speechiness_max"])
        if intent.get("tempo_min") is not None:
            _add("tempo", ">=", intent["tempo_min"])
        if intent.get("tempo_max") is not None:
            _add("tempo", "<=", intent["tempo_max"])
        if intent.get("popularity_min") is not None:
            _add("popularity", ">=", intent["popularity_min"])
        if intent.get("popularity_max") is not None:
            _add("popularity", "<=", intent["popularity_max"])

        if intent.get("genre_query"):
            wh.append("LOWER(dg.nombre_genero) LIKE ?")
            params.append(f"%{intent['genre_query']}%")
        if intent.get("artist_query"):
            wh.append("LOWER(da.nombre_artista) LIKE ?")
            params.append(f"%{intent['artist_query']}%")

        keywords = intent.get("keywords") or []
        for kw in keywords[:3]:
            wh.append("(LOWER(dt.nombre_track) LIKE ? OR LOWER(da.nombre_artista) LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        where_sql = " AND ".join(wh) if wh else "1=1"
        sql = f"""
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista, dt.popularity,
                   dt.energy, dt.danceability, dt.valence, dt.acousticness
            FROM dim_track dt
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
            WHERE {where_sql}
            ORDER BY dt.popularity DESC NULLS LAST
            LIMIT ?
        """
        params.append(limit)
        try:
            rows = self._conn.execute(sql, params).fetchall()
            cols = [d[0] for d in self._conn.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception:
            if user_id:
                wh_user = _warehouse_user_id(user_id)
                return RankingEngine(self._conn).rank_for_user(user_id, wh_user, limit=limit)
            return []

    def _fetch_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        if not table_exists_conn(self._conn, "dim_track"):
            return None
        row = self._conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista, dt.popularity
            FROM dim_track dt
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE dt.id_track = ?
            """,
            [track_id],
        ).fetchone()
        if not row:
            return None
        return {"id_track": row[0], "nombre_track": row[1], "nombre_artista": row[2], "popularity": row[3]}

    def _enrich_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        tid = track.get("id_track")
        if not tid or not table_exists_conn(self._conn, "dim_track"):
            return track
        row = self._conn.execute(
            "SELECT energy, danceability, valence, acousticness, popularity FROM dim_track WHERE id_track = ?",
            [tid],
        ).fetchone()
        if row:
            track = {**track, "energy": row[0], "danceability": row[1], "valence": row[2], "acousticness": row[3], "popularity": row[4]}
        return track


def _avg_from_top(tracks: List[Dict[str, Any]]) -> float:
    if not tracks:
        return 50.0
    return sum(float(t.get("popularity") or 0) for t in tracks) / len(tracks)
