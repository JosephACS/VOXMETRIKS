from __future__ import annotations

from app.core.cache import cache_get, cache_set, make_cache_key
from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import (
    DailyStreamsResponse,
    GenreAnalyticsItem,
    GenresAnalyticsResponse,
    PlatformUsageItem,
    PlatformUsageResponse,
    TopArtistItem,
    TopArtistsResponse,
    TopTrackItem,
    TopTracksResponse,
)
from app.services._warehouse import agg_daily_skip_rate_sql, normalize_skip_rate, table_exists

logger = get_logger(__name__)

ANALYTICS_CACHE_TTL = 90.0


class AnalyticsService:
    """Analytics domain — GOLD pre-aggregated KPIs only."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    def get_daily_streams(self) -> DailyStreamsResponse:
        key = make_cache_key("analytics.daily_streams")
        hit = cache_get(key)
        if hit is not None:
            return hit

        if not table_exists(self._client, "agg_daily_streams"):
            logger.warning("analytics_daily_streams: GOLD table missing")
            empty = DailyStreamsResponse(
                total_streams=0,
                unique_users=0,
                unique_tracks=0,
                avg_duration_ms=0.0,
                skip_rate=0.0,
            )
            cache_set(key, empty, ANALYTICS_CACHE_TTL)
            return empty

        skip_sql = agg_daily_skip_rate_sql(self._client)
        row = self._client.fetch_one(
            f"""
            SELECT fecha, total_streams, unique_users, unique_tracks,
                   avg_duration_ms, {skip_sql} AS skip_rate
            FROM agg_daily_streams
            ORDER BY fecha DESC
            LIMIT 1
            """,
            label="analytics_daily_streams_latest",
        )
        result = DailyStreamsResponse(
            fecha=row.get("fecha") if row else None,
            total_streams=int(row.get("total_streams") or 0) if row else 0,
            unique_users=int(row.get("unique_users") or 0) if row else 0,
            unique_tracks=int(row.get("unique_tracks") or 0) if row else 0,
            avg_duration_ms=float(row.get("avg_duration_ms") or 0) if row else 0.0,
            skip_rate=normalize_skip_rate(row.get("skip_rate")) if row else 0.0,
        )
        cache_set(key, result, ANALYTICS_CACHE_TTL)
        return result

    def get_top_artists(self, *, limit: int = 20) -> TopArtistsResponse:
        if not table_exists(self._client, "agg_artist_growth"):
            return TopArtistsResponse(items=[], count=0)

        rows = self._client.fetch_all(
            """
            SELECT
                id_artista,
                nombre_artista AS nombre,
                streams_7d,
                growth_pct,
                total_followers
            FROM agg_artist_growth
            ORDER BY streams_7d DESC, growth_pct DESC
            LIMIT ?
            """,
            [limit],
            label="analytics_top_artists",
        )
        items = [
            TopArtistItem(
                id_artista=int(r["id_artista"]),
                nombre=str(r["nombre"] or ""),
                streams_7d=int(r["streams_7d"] or 0),
                growth_pct=float(r["growth_pct"] or 0),
                total_followers=int(r["total_followers"]) if r.get("total_followers") is not None else None,
            )
            for r in rows
        ]
        return TopArtistsResponse(items=items, count=len(items))

    def get_top_tracks(self, *, limit: int = 20) -> TopTracksResponse:
        if not table_exists(self._client, "agg_tracks_populares"):
            return TopTracksResponse(items=[], count=0)

        rows = self._client.fetch_all(
            """
            SELECT
                id_track,
                nombre_track AS track_name,
                nombre_artista AS artist,
                popularity,
                engagement_score,
                total_streams
            FROM agg_tracks_populares
            ORDER BY total_streams DESC, popularity DESC
            LIMIT ?
            """,
            [limit],
            label="analytics_top_tracks",
        )
        items = [
            TopTrackItem(
                id_track=int(r["id_track"]),
                track_name=str(r["track_name"] or ""),
                artist=str(r["artist"] or ""),
                popularity=int(r["popularity"] or 0),
                engagement_score=float(r["engagement_score"] or 0),
                total_streams=int(r["total_streams"]) if r.get("total_streams") is not None else None,
            )
            for r in rows
        ]
        return TopTracksResponse(items=items, count=len(items))

    def get_genres(self, *, limit: int = 50) -> GenresAnalyticsResponse:
        if not table_exists(self._client, "agg_genero_popularidad"):
            return GenresAnalyticsResponse(items=[], count=0)

        rows = self._client.fetch_all(
            """
            SELECT
                id_genero,
                nombre_genero AS genre,
                popularidad_promedio AS popularity,
                energia_promedio AS energy_avg,
                total_tracks
            FROM agg_genero_popularidad
            ORDER BY popularidad_promedio DESC, total_tracks DESC
            LIMIT ?
            """,
            [limit],
            label="analytics_genres",
        )
        items = [
            GenreAnalyticsItem(
                id_genero=int(r["id_genero"]),
                genre=str(r["genre"] or ""),
                popularity=float(r["popularity"] or 0),
                energy_avg=float(r["energy_avg"] or 0),
                total_tracks=int(r["total_tracks"] or 0),
            )
            for r in rows
        ]
        return GenresAnalyticsResponse(items=items, count=len(items))

    def get_platform_usage(self, *, limit: int = 20) -> PlatformUsageResponse:
        if not table_exists(self._client, "agg_platform_usage"):
            return PlatformUsageResponse(items=[], count=0)

        rows = self._client.fetch_all(
            """
            SELECT
                platform,
                device_type,
                session_count,
                total_streams,
                avg_session_min,
                share_pct
            FROM agg_platform_usage
            ORDER BY share_pct DESC, total_streams DESC
            LIMIT ?
            """,
            [limit],
            label="analytics_platform_usage",
        )
        items = [
            PlatformUsageItem(
                platform=str(r["platform"] or "unknown"),
                device_type=str(r["device_type"] or "unknown"),
                session_count=int(r["session_count"] or 0),
                total_streams=int(r["total_streams"] or 0),
                avg_session_min=float(r["avg_session_min"] or 0),
                share_pct=float(r["share_pct"] or 0),
            )
            for r in rows
        ]
        return PlatformUsageResponse(items=items, count=len(items))
