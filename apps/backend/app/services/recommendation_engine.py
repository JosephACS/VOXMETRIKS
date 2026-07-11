from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.cache import cache_get, cache_set, make_cache_key, ttl_for
from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.services._warehouse import table_exists
from app.services.scoring.collaborative_filter import CollaborativeFilter
from app.services.scoring.engagement_scoring import (
    blend_engagement,
    score_track_engagement,
    score_user_engagement_signal,
)
from app.services.scoring.popularity_scoring import score_popularity
from app.services.scoring.trending_boost import TrendingBoost

logger = get_logger(__name__)

CANDIDATE_POOL = 1000
RERANK_POOL = 50
DEFAULT_LIMIT = 20

W_POPULARITY = 0.35
W_ENGAGEMENT = 0.25
W_COLLABORATIVE = 0.20
W_TRENDING = 0.20


@dataclass
class UserContext:
    user_id: int
    total_plays: int = 0
    total_skips: int = 0
    total_likes: int = 0
    skip_rate: float = 0.0
    engagement_score: float = 0.0
    listened_tracks: dict[int, int] = field(default_factory=dict)
    top_genres: dict[int, float] = field(default_factory=dict)
    top_genre_names: dict[int, str] = field(default_factory=dict)
    top_artists: set[int] = field(default_factory=set)
    top_artist_names: dict[int, str] = field(default_factory=dict)
    preferred_device: str | None = None
    preferred_platform: str | None = None
    exists: bool = False


@dataclass
class ScoredRecommendation:
    track_id: int
    track_name: str
    artist: str
    score: float
    reason: str
    popularity: int = 0
    engagement_score: float = 0.0
    factors: dict[str, float] = field(default_factory=dict)


class RecommendationEngine:
    """
    Deterministic heuristic recommender — SQL aggregates + weighted scoring.
    No ML. Fully explainable. Ready for future hybrid/embedding layer.
    """

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()
        self._collab = CollaborativeFilter(self._client)
        self._trending = TrendingBoost(self._client)

    def recommend(self, user_id: int, *, limit: int = DEFAULT_LIMIT) -> list[ScoredRecommendation]:
        cache_key = make_cache_key("enterprise.rec.engine", user_id, limit)
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        ctx = self._load_user_context(user_id)
        candidates = self._fetch_candidates(CANDIDATE_POOL)
        if not candidates:
            return []

        collab_scores = self._collab.load_track_scores(user_id)
        self._trending.ensure_loaded()

        pops = [float(c.get("popularity") or 0) for c in candidates]
        engs = [float(c.get("track_engagement") or 0) for c in candidates]
        min_pop, max_pop = min(pops), max(pops)
        min_eng, max_eng = min(engs), max(engs)
        user_signal = score_user_engagement_signal(
            total_plays=ctx.total_plays,
            total_skips=ctx.total_skips,
            total_likes=ctx.total_likes,
            warehouse_engagement=ctx.engagement_score if ctx.engagement_score else None,
        )

        scored: list[ScoredRecommendation] = []
        for row in candidates:
            track_id = int(row["id_track"])
            if track_id in ctx.listened_tracks and ctx.listened_tracks.get(track_id, 0) >= 5:
                continue

            pop_s = score_popularity(
                float(row.get("popularity") or 0),
                min_pop=min_pop,
                max_pop=max_pop,
                in_top_chart=bool(row.get("in_top_chart")),
                playlist_boost=bool(row.get("playlist_boost")),
            )
            track_eng = score_track_engagement(
                global_engagement=float(row.get("track_engagement") or 0),
                min_eng=min_eng,
                max_eng=max_eng,
            )
            eng_s = blend_engagement(track_eng, user_signal, skip_penalty=ctx.skip_rate)
            collab_s = collab_scores.get(track_id, 0.0)
            trend_s = self._trending.score_track(
                artist_id=int(row["id_artista"]) if row.get("id_artista") is not None else None,
                genre_id=int(row["id_genero"]) if row.get("id_genero") is not None else None,
            )

            final = (
                pop_s * W_POPULARITY
                + eng_s * W_ENGAGEMENT
                + collab_s * W_COLLABORATIVE
                + trend_s * W_TRENDING
            )
            factors = {
                "popularity": pop_s,
                "engagement": eng_s,
                "collaborative": collab_s,
                "trending": trend_s,
            }
            scored.append(
                ScoredRecommendation(
                    track_id=track_id,
                    track_name=str(row.get("track_name") or row.get("nombre_track") or ""),
                    artist=str(row.get("artist") or row.get("nombre_artista") or ""),
                    score=round(final, 4),
                    reason=self._reason_code(factors),
                    popularity=int(row.get("popularity") or 0),
                    engagement_score=round(eng_s, 4),
                    factors=factors,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        top = scored[: max(limit, RERANK_POOL)][:limit]
        cache_set(cache_key, top, ttl_for("recommendations"))
        return top

    def build_user_profile(self, user_id: int) -> UserContext:
        """Full user context for diagnostics and tests."""
        ctx = self._load_user_context(user_id)
        events = self._events_table()
        if table_exists(self._client, events):
            ctx.top_genres, ctx.top_genre_names = self._genre_affinity(user_id, events)
            ctx.top_artists, ctx.top_artist_names = self._artist_affinity(user_id, events)
        if table_exists(self._client, "fact_streaming"):
            device_row = self._client.fetch_one(
                """
                SELECT device_type, platform
                FROM fact_streaming
                WHERE id_usuario = ?
                GROUP BY device_type, platform
                ORDER BY COUNT(*) DESC
                LIMIT 1
                """,
                [user_id],
                label="rec_profile_device",
            )
            if device_row:
                ctx.preferred_device = device_row.get("device_type")
                ctx.preferred_platform = device_row.get("platform")
        return ctx

    def _genre_affinity(
        self, user_id: int, events: str
    ) -> tuple[dict[int, float], dict[int, str]]:
        if not table_exists(self._client, "dim_track"):
            return {}, {}
        rows = self._client.fetch_all(
            f"""
            SELECT dt.id_genero, dg.nombre_genero, COUNT(*) AS plays
            FROM {events} fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
            WHERE fs.id_usuario = ? AND dt.id_genero IS NOT NULL
            GROUP BY dt.id_genero, dg.nombre_genero
            ORDER BY plays DESC
            LIMIT 5
            """,
            [user_id],
            label="rec_genre_affinity",
        )
        if not rows:
            return {}, {}
        total = sum(int(r["plays"]) for r in rows) or 1
        weights = {int(r["id_genero"]): int(r["plays"]) / total for r in rows}
        names = {int(r["id_genero"]): str(r["nombre_genero"] or "") for r in rows}
        return weights, names

    def _artist_affinity(
        self, user_id: int, events: str
    ) -> tuple[set[int], dict[int, str]]:
        if not table_exists(self._client, "dim_track"):
            return set(), {}
        rows = self._client.fetch_all(
            f"""
            SELECT dt.id_artista, da.nombre_artista, COUNT(*) AS plays
            FROM {events} fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE fs.id_usuario = ? AND dt.id_artista IS NOT NULL
            GROUP BY dt.id_artista, da.nombre_artista
            ORDER BY plays DESC
            LIMIT 10
            """,
            [user_id],
            label="rec_artist_affinity",
        )
        artists = {int(r["id_artista"]) for r in rows}
        names = {int(r["id_artista"]): str(r["nombre_artista"] or "") for r in rows}
        return artists, names

    def _load_user_context(self, user_id: int) -> UserContext:
        ctx = UserContext(user_id=user_id)

        if table_exists(self._client, "dim_usuario"):
            exists = self._client.fetch_scalar(
                "SELECT COUNT(*) FROM dim_usuario WHERE id_usuario = ?",
                [user_id],
                label="rec_user_dim_exists",
            )
            ctx.exists = bool(exists and int(exists) > 0)

        if table_exists(self._client, "agg_user_activity"):
            row = self._client.fetch_one(
                """
                SELECT total_plays, total_skips, total_likes, engagement_score
                FROM agg_user_activity WHERE id_usuario = ?
                """,
                [user_id],
                label="rec_user_activity_agg",
            )
            if row:
                ctx.total_plays = int(row.get("total_plays") or 0)
                ctx.total_skips = int(row.get("total_skips") or 0)
                ctx.total_likes = int(row.get("total_likes") or 0)
                ctx.engagement_score = float(row.get("engagement_score") or 0)
                ctx.exists = True

        if table_exists(self._client, "fact_user_activity"):
            row = self._client.fetch_one(
                """
                SELECT COUNT(*) AS events FROM fact_user_activity WHERE id_usuario = ?
                """,
                [user_id],
                label="rec_user_fact_activity",
            )
            if row and int(row.get("events") or 0) > 0:
                ctx.exists = True

        events = self._events_table()
        if table_exists(self._client, events):
            rows = self._client.fetch_all(
                f"""
                SELECT id_track, COUNT(*) AS plays
                FROM {events}
                WHERE id_usuario = ? AND id_track IS NOT NULL
                GROUP BY id_track
                """,
                [user_id],
                label="rec_user_listened",
            )
            ctx.listened_tracks = {int(r["id_track"]): int(r["plays"]) for r in rows}
            ctx.total_plays = ctx.total_plays or sum(ctx.listened_tracks.values())
            if ctx.listened_tracks:
                ctx.exists = True

            if table_exists(self._client, "fact_streaming"):
                skip_expr = self._skip_count_expr()
                if skip_expr:
                    skip_row = self._client.fetch_one(
                        f"""
                        SELECT COUNT(*) AS total, {skip_expr} AS skips
                        FROM fact_streaming WHERE id_usuario = ?
                        """,
                        [user_id],
                        label="rec_user_skips",
                    )
                    if skip_row and int(skip_row.get("total") or 0) > 0:
                        ctx.total_skips = int(skip_row.get("skips") or 0)
                        ctx.skip_rate = round(ctx.total_skips / int(skip_row["total"]), 4)

        return ctx

    def _fetch_candidates(self, limit: int) -> list[dict[str, Any]]:
        top_chart_ids: set[int] = set()
        playlist_ids: set[int] = set()

        if table_exists(self._client, "agg_tracks_populares"):
            top_rows = self._client.fetch_all(
                """
                SELECT id_track FROM agg_tracks_populares
                ORDER BY popularity DESC NULLS LAST
                LIMIT 50
                """,
                label="rec_top_chart_ids",
            )
            top_chart_ids = {int(r["id_track"]) for r in top_rows}

        if table_exists(self._client, "agg_top_playlists") and table_exists(
            self._client, "fact_streaming"
        ):
            cols = {
                r[0].lower()
                for r in self._client.connect().execute("DESCRIBE fact_streaming").fetchall()
            }
            if "id_playlist" in cols:
                pl_rows = self._client.fetch_all(
                    """
                    SELECT DISTINCT fs.id_track
                    FROM fact_streaming fs
                    INNER JOIN (
                        SELECT id_playlist FROM agg_top_playlists
                        ORDER BY total_plays DESC LIMIT 10
                    ) tp ON fs.id_playlist = tp.id_playlist
                    WHERE fs.id_track IS NOT NULL
                    LIMIT 200
                    """,
                    label="rec_playlist_boost_ids",
                )
                playlist_ids = {int(r["id_track"]) for r in pl_rows if r.get("id_track")}

        if table_exists(self._client, "agg_tracks_populares"):
            stream_join = ""
            stream_select = "0 AS total_streams"
            if table_exists(self._client, "fact_streaming"):
                stream_join = """
                LEFT JOIN (
                    SELECT id_track, SUM(COALESCE(streams, 1)) AS total_streams
                    FROM fact_streaming
                    GROUP BY id_track
                ) fs ON fs.id_track = atp.id_track
                """
                stream_select = "COALESCE(fs.total_streams, 0) AS total_streams"

            rows = self._client.fetch_all(
                f"""
                SELECT
                    atp.id_track,
                    atp.nombre_track AS track_name,
                    atp.nombre_artista AS artist,
                    atp.popularity,
                    COALESCE(atp.popularity, 0) * 1.0 AS track_engagement,
                    dt.id_genero,
                    dt.id_artista,
                    {stream_select}
                FROM agg_tracks_populares atp
                LEFT JOIN dim_track dt ON dt.id_track = atp.id_track
                {stream_join}
                ORDER BY total_streams DESC, atp.popularity DESC
                LIMIT ?
                """,
                [limit],
                label="rec_candidates_pool",
            )
        elif table_exists(self._client, "agg_recommendation_scores"):
            rows = self._client.fetch_all(
                """
                SELECT
                    rs.id_track,
                    rs.nombre_track AS track_name,
                    '' AS artist,
                    rs.popularity,
                    rs.engagement_score AS track_engagement,
                    dt.id_genero,
                    dt.id_artista,
                    0 AS total_streams
                FROM agg_recommendation_scores rs
                LEFT JOIN dim_track dt ON dt.id_track = rs.id_track
                ORDER BY rs.recommendation_score DESC
                LIMIT ?
                """,
                [limit],
                label="rec_candidates_scores",
            )
        elif table_exists(self._client, "dim_track"):
            rows = self._client.fetch_all(
                """
                SELECT
                    dt.id_track,
                    dt.nombre_track AS track_name,
                    da.nombre_artista AS artist,
                    COALESCE(dt.popularity, 0) AS popularity,
                    COALESCE(dt.popularity, 0) * 1.0 AS track_engagement,
                    dt.id_genero,
                    dt.id_artista,
                    0 AS total_streams
                FROM dim_track dt
                LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
                ORDER BY dt.popularity DESC NULLS LAST
                LIMIT ?
                """,
                [limit],
                label="rec_candidates_dim",
            )
        else:
            return []

        for row in rows:
            tid = int(row["id_track"])
            row["in_top_chart"] = tid in top_chart_ids
            row["playlist_boost"] = tid in playlist_ids
        return rows

    def _events_table(self) -> str:
        if table_exists(self._client, "silver_streams"):
            return "silver_streams"
        return "fact_streaming"

    def _skip_count_expr(self) -> str | None:
        if not table_exists(self._client, "fact_streaming"):
            return None
        cols = {
            r[0].lower()
            for r in self._client.connect().execute("DESCRIBE fact_streaming").fetchall()
        }
        if "skipped" in cols:
            return "SUM(CASE WHEN COALESCE(skipped, FALSE) THEN 1 ELSE 0 END)"
        return None

    @staticmethod
    def _reason_code(factors: dict[str, float]) -> str:
        ranked = sorted(factors.items(), key=lambda kv: kv[1], reverse=True)
        primary, pval = ranked[0]
        secondary = ranked[1][0] if len(ranked) > 1 else None

        if primary == "collaborative" and pval >= 0.45:
            return "high_engagement_similar_users"
        if primary == "trending" and pval >= 0.45:
            return "trending_artist_genre"
        if primary == "engagement" and pval >= 0.5:
            return "high_engagement"
        if primary == "popularity" and pval >= 0.55:
            return "high_popularity"
        if secondary == "collaborative" and factors.get("collaborative", 0) >= 0.35:
            return "similar_users_plus_trending"
        if factors.get("trending", 0) >= 0.4 and factors.get("popularity", 0) >= 0.4:
            return "trending_popular_pick"
        return "catalog_discovery"
