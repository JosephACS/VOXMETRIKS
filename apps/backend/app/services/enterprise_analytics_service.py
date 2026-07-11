from __future__ import annotations

from datetime import date

from app.core.cache import cache_get, cache_set, make_cache_key, ttl_for
from app.core.logging import get_logger
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import PeakHourItem, StreamSeriesPoint, StreamsAnalyticsData
from app.schemas.dashboard import (
    DashboardOverviewData,
    DeviceUsageItem,
    GenreTrendItem,
    GrowthTrendPoint,
)

logger = get_logger(__name__)


class EnterpriseAnalyticsService:
    """Analytics domain — GOLD aggregates via repository layer."""

    def __init__(self, repo: AnalyticsRepository | None = None) -> None:
        self._repo = repo or AnalyticsRepository()

    def get_streams_analytics(self, start_date: date, end_date: date) -> StreamsAnalyticsData:
        cache_key = make_cache_key("enterprise.analytics.streams", start_date, end_date)
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        series_rows = self._repo.get_streams_series(start_date, end_date)
        series = [
            StreamSeriesPoint(
                fecha=r["fecha"],
                total_streams=int(r.get("total_streams") or 0),
                unique_users=int(r.get("unique_users") or 0),
                skip_count=int(r.get("skip_count") or 0),
                avg_duration_ms=float(r.get("avg_duration_ms") or 0),
            )
            for r in series_rows
        ]

        peak_hours = [
            PeakHourItem(
                hour_of_day=int(r["hour_of_day"]),
                stream_count=int(r.get("stream_count") or 0),
            )
            for r in self._repo.get_peak_hours(start_date, end_date)
        ]

        result = StreamsAnalyticsData(
            start_date=start_date,
            end_date=end_date,
            series=series,
            peak_hours=peak_hours,
            trending_artists=self._repo.get_trending_artists(limit=10),
            top_genres=self._repo.get_genre_trends(limit=10),
            device_breakdown=self._repo.get_device_breakdown(limit=10),
        )
        cache_set(cache_key, result, ttl_for("analytics"))
        return result

    def get_dashboard_overview(self) -> DashboardOverviewData:
        cache_key = make_cache_key("enterprise.dashboard.overview")
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        totals = self._repo.get_latest_daily_totals() or {}
        growth_rows = list(reversed(self._repo.get_growth_trends(days=30)))

        genres = [
            GenreTrendItem(
                id_genero=int(g["id_genero"]),
                nombre_genero=str(g.get("nombre_genero") or ""),
                streams_7d=int(g.get("streams_7d") or 0),
                trend_pct=float(g.get("trend_pct") or 0),
            )
            for g in self._repo.get_genre_trends(limit=5)
        ]

        devices = [
            DeviceUsageItem(
                platform=str(d.get("platform") or "unknown"),
                device_type=str(d.get("device_type") or "unknown"),
                total_streams=int(d.get("total_streams") or 0),
                share_pct=float(d.get("share_pct") or 0),
            )
            for d in self._repo.get_device_breakdown(limit=8)
        ]

        growth_trends = [
            GrowthTrendPoint(
                fecha=r["fecha"],
                total_streams=int(r.get("total_streams") or 0),
                unique_users=int(r.get("unique_users") or 0),
            )
            for r in growth_rows
        ]

        result = DashboardOverviewData(
            total_streams=int(totals.get("total_streams") or 0),
            active_users=int(totals.get("active_users") or 0),
            top_genres=genres,
            top_artists=self._repo.get_trending_artists(limit=10),
            device_usage=devices,
            growth_trends=growth_trends,
        )
        cache_set(cache_key, result, ttl_for("dashboard"))
        return result
