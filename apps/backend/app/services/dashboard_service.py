"""Dashboard aggregates — GOLD + cache only, frontend-ready."""

from __future__ import annotations

import json
from typing import Any

from app.core.cache import cache_get, cache_set, make_cache_key
from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import (
    DashboardEngagementResponse,
    DashboardGrowthResponse,
    DashboardOverviewResponse,
    DashboardRealtimeResponse,
    DeviceShareItem,
    GrowthArtistItem,
    LiveTrackItem,
    UserSegmentItem,
)
from app.services._warehouse import agg_daily_skip_rate_sql, normalize_skip_rate, table_exists

logger = get_logger(__name__)

CACHE_TTL_OVERVIEW = 120.0
CACHE_TTL_REALTIME = 30.0
CACHE_TTL_GROWTH = 180.0
CACHE_TTL_ENGAGEMENT = 180.0


class DashboardService:
    """Fast dashboard reads — pre-aggregated GOLD, optional agg_dashboard_cache."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    def get_overview(self) -> DashboardOverviewResponse:
        key = make_cache_key("dashboard.overview")
        cached = cache_get(key)
        if cached is not None:
            return cached

        row = self._cache_row("overview")
        if row:
            result = DashboardOverviewResponse(
                total_streams=int(row.get("total_streams") or 0),
                active_users=int(row.get("active_users") or 0),
                total_tracks=int(row.get("total_tracks") or 0),
                top_genre=str(row.get("top_genre") or "unknown"),
                avg_session_time=float(row.get("avg_session_min") or 0),
                skip_rate=float(row.get("skip_rate") or 0),
            )
            cache_set(key, result, CACHE_TTL_OVERVIEW)
            return result

        result = self._overview_from_gold()
        cache_set(key, result, CACHE_TTL_OVERVIEW)
        return result

    def get_realtime(self) -> DashboardRealtimeResponse:
        key = make_cache_key("dashboard.realtime")
        cached = cache_get(key)
        if cached is not None:
            return cached

        streams_60m = users_60m = 0
        if table_exists(self._client, "fact_streaming"):
            row = self._client.fetch_one(
                """
                SELECT
                    COUNT(*) AS streams_60m,
                    COUNT(DISTINCT id_usuario) AS users_60m
                FROM fact_streaming
                WHERE fecha_evento >= CURRENT_TIMESTAMP - INTERVAL 60 MINUTE
                """,
                label="dashboard_realtime_streams",
            )
            if row:
                streams_60m = int(row.get("streams_60m") or 0)
                users_60m = int(row.get("users_60m") or 0)
        elif table_exists(self._client, "agg_dashboard_cache"):
            row = self._cache_row("hourly")
            if row:
                streams_60m = int(row.get("streams_60m") or 0)

        top_tracks = self._top_live_tracks(limit=10)
        devices = self._device_distribution(limit=5)

        result = DashboardRealtimeResponse(
            streams_last_60m=streams_60m,
            active_users=users_60m,
            top_tracks_live=top_tracks,
            device_distribution=devices,
        )
        cache_set(key, result, CACHE_TTL_REALTIME)
        return result

    def get_growth(self) -> DashboardGrowthResponse:
        key = make_cache_key("dashboard.growth")
        cached = cache_get(key)
        if cached is not None:
            return cached

        row = self._cache_row("growth")
        user_growth = stream_growth = weekly_pct = 0.0
        top_artists: list[dict[str, Any]] = []

        if row:
            weekly_pct = float(row.get("growth_pct_weekly") or 0)
            payload = row.get("payload_json")
            if payload:
                data = json.loads(payload) if isinstance(payload, str) else payload
                top_artists = data.get("top_artists", [])

        if table_exists(self._client, "agg_daily_streams"):
            w = self._client.fetch_one(
                """
                WITH bounds AS (SELECT MAX(fecha) AS max_d FROM agg_daily_streams),
                cur AS (
                    SELECT COALESCE(SUM(total_streams), 0) AS s,
                           COALESCE(SUM(unique_users), 0) AS u
                    FROM agg_daily_streams, bounds
                    WHERE fecha > max_d - INTERVAL 7 DAY
                ),
                prev AS (
                    SELECT COALESCE(SUM(total_streams), 0) AS s,
                           COALESCE(SUM(unique_users), 0) AS u
                    FROM agg_daily_streams, bounds
                    WHERE fecha <= max_d - INTERVAL 7 DAY
                      AND fecha > max_d - INTERVAL 14 DAY
                )
                SELECT
                    cur.s AS streams_7d, prev.s AS streams_prev_7d,
                    cur.u AS users_7d, prev.u AS users_prev_7d
                FROM cur, prev
                """,
                label="dashboard_growth_weekly",
            )
            if w:
                sp, pp = int(w.get("streams_prev_7d") or 0), int(w.get("users_prev_7d") or 0)
                sc, uc = int(w.get("streams_7d") or 0), int(w.get("users_7d") or 0)
                stream_growth = round((sc - sp) * 100.0 / sp, 1) if sp else 0.0
                user_growth = round((uc - pp) * 100.0 / pp, 1) if pp else 0.0
                if not weekly_pct and sp:
                    weekly_pct = stream_growth

        if not top_artists and table_exists(self._client, "agg_artist_growth"):
            top_artists = self._client.fetch_all(
                """
                SELECT id_artista, nombre_artista AS nombre, streams_7d, growth_pct
                FROM agg_artist_growth
                ORDER BY growth_pct DESC, streams_7d DESC
                LIMIT 10
                """,
                label="dashboard_growth_artists",
            )

        artist_items = [
            GrowthArtistItem(
                id_artista=int(a["id_artista"]),
                nombre=str(a.get("nombre") or a.get("nombre_artista") or ""),
                streams_7d=int(a.get("streams_7d") or 0),
                growth_pct=float(a.get("growth_pct") or 0),
            )
            for a in top_artists
        ]

        result = DashboardGrowthResponse(
            user_growth_pct=user_growth,
            stream_growth_pct=stream_growth if stream_growth else weekly_pct,
            weekly_growth_pct=weekly_pct,
            top_artists=artist_items,
        )
        cache_set(key, result, CACHE_TTL_GROWTH)
        return result

    def get_engagement(self) -> DashboardEngagementResponse:
        key = make_cache_key("dashboard.engagement")
        cached = cache_get(key)
        if cached is not None:
            return cached

        segments: list[UserSegmentItem] = []
        row = self._cache_row("engagement")
        if row and row.get("payload_json"):
            for s in json.loads(row["payload_json"]):
                segments.append(UserSegmentItem(**s))

        if not segments and table_exists(self._client, "agg_user_engagement"):
            rows = self._client.fetch_all(
                """
                SELECT segment, user_count, avg_plays, avg_session_min, retention_pct
                FROM agg_user_engagement
                ORDER BY avg_plays DESC
                """,
                label="dashboard_engagement_segments",
            )
            segments = [
                UserSegmentItem(
                    segment=str(r["segment"]),
                    user_count=int(r["user_count"] or 0),
                    avg_plays=float(r["avg_plays"] or 0),
                    avg_session_min=float(r["avg_session_min"] or 0),
                    retention_pct=float(r["retention_pct"] or 0),
                )
                for r in rows
            ]

        total_users = sum(s.user_count for s in segments) or 1
        power = next((s.user_count for s in segments if s.segment == "power_users"), 0)
        power_pct = round(100.0 * power / total_users, 1)
        avg_engagement = 0.0
        retention = 0.0
        if segments:
            avg_engagement = round(sum(s.avg_plays for s in segments) / len(segments), 2)
            retention = round(sum(s.retention_pct for s in segments) / len(segments), 1)

        if table_exists(self._client, "agg_tracks_populares"):
            eng = self._client.fetch_scalar(
                "SELECT ROUND(AVG(engagement_score), 2) FROM agg_tracks_populares",
                label="dashboard_avg_engagement",
            )
            if eng:
                avg_engagement = float(eng)

        result = DashboardEngagementResponse(
            segments=segments,
            power_users_pct=power_pct,
            avg_engagement_score=avg_engagement,
            retention_proxy=retention,
        )
        cache_set(key, result, CACHE_TTL_ENGAGEMENT)
        return result

    def _cache_row(self, cache_type: str) -> dict[str, Any] | None:
        if not table_exists(self._client, "agg_dashboard_cache"):
            return None
        return self._client.fetch_one(
            """
            SELECT * FROM agg_dashboard_cache
            WHERE cache_type = ?
            ORDER BY computed_at DESC
            LIMIT 1
            """,
            [cache_type],
            label=f"dashboard_cache_{cache_type}",
        )

    def _overview_from_gold(self) -> DashboardOverviewResponse:
        total_streams = active_users = 0
        skip_rate = 0.0
        avg_duration = 0.0

        if table_exists(self._client, "agg_daily_streams"):
            skip_sql = agg_daily_skip_rate_sql(self._client)
            row = self._client.fetch_one(
                f"""
                SELECT total_streams, unique_users, avg_duration_ms, {skip_sql} AS skip_rate
                FROM agg_daily_streams
                ORDER BY fecha DESC
                LIMIT 1
                """,
                label="dashboard_overview_daily",
            )
            if row:
                total_streams = int(row.get("total_streams") or 0)
                active_users = int(row.get("unique_users") or 0)
                avg_duration = float(row.get("avg_duration_ms") or 0) / 60_000.0
                skip_rate = normalize_skip_rate(row.get("skip_rate"))

        total_tracks = 0
        if table_exists(self._client, "dim_track"):
            total_tracks = int(
                self._client.fetch_scalar("SELECT COUNT(*) FROM dim_track", label="dashboard_track_count") or 0
            )

        top_genre = "unknown"
        if table_exists(self._client, "agg_genero_popularidad"):
            row = self._client.fetch_one(
                """
                SELECT nombre_genero FROM agg_genero_popularidad
                ORDER BY popularidad_promedio DESC LIMIT 1
                """,
                label="dashboard_top_genre",
            )
            if row:
                top_genre = str(row.get("nombre_genero") or "unknown")

        avg_session = avg_duration
        if table_exists(self._client, "agg_user_engagement"):
            row = self._client.fetch_scalar(
                "SELECT ROUND(AVG(avg_session_min), 1) FROM agg_user_engagement",
                label="dashboard_avg_session",
            )
            if row:
                avg_session = float(row)

        return DashboardOverviewResponse(
            total_streams=total_streams,
            active_users=active_users,
            total_tracks=total_tracks,
            top_genre=top_genre,
            avg_session_time=avg_session,
            skip_rate=skip_rate,
        )

    def _top_live_tracks(self, *, limit: int) -> list[LiveTrackItem]:
        if not table_exists(self._client, "agg_tracks_populares"):
            return []
        rows = self._client.fetch_all(
            """
            SELECT id_track, nombre_track AS track_name, nombre_artista AS artist,
                   total_streams, engagement_score
            FROM agg_tracks_populares
            ORDER BY total_streams DESC, engagement_score DESC
            LIMIT ?
            """,
            [limit],
            label="dashboard_live_tracks",
        )
        return [
            LiveTrackItem(
                track_id=int(r["id_track"]),
                track_name=str(r["track_name"] or ""),
                artist=str(r["artist"] or ""),
                streams=int(r["total_streams"] or 0),
                engagement_score=float(r["engagement_score"] or 0),
            )
            for r in rows
        ]

    def _device_distribution(self, *, limit: int) -> list[DeviceShareItem]:
        if not table_exists(self._client, "agg_platform_usage"):
            return []
        rows = self._client.fetch_all(
            """
            SELECT platform, device_type, share_pct, total_streams
            FROM agg_platform_usage
            ORDER BY share_pct DESC
            LIMIT ?
            """,
            [limit],
            label="dashboard_device_share",
        )
        return [
            DeviceShareItem(
                platform=str(r["platform"] or "unknown"),
                device_type=str(r["device_type"] or "unknown"),
                share_pct=float(r["share_pct"] or 0),
                total_streams=int(r["total_streams"] or 0),
            )
            for r in rows
        ]
