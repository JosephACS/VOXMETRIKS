from __future__ import annotations

from datetime import date
from typing import Any

from app.repositories.base_repository import BaseRepository


class AnalyticsRepository(BaseRepository):
    """GOLD-layer analytics reads."""

    def get_streams_series(self, start: date, end: date) -> list[dict[str, Any]]:
        if self.table_exists("agg_daily_streams"):
            skip_count_sql = self._agg_daily_skip_count_expr()
            rows = self.fetch_all(
                f"""
                SELECT
                    fecha,
                    total_streams,
                    unique_users,
                    {skip_count_sql} AS skip_count,
                    avg_duration_ms
                FROM agg_daily_streams
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha ASC
                """,
                [start, end],
                label="repo_streams_series",
            )
            if rows:
                return rows
        return self._streams_series_from_fact(start, end)

    def _agg_daily_skip_count_expr(self) -> str:
        from app.services._warehouse import agg_daily_skip_count_sql
        from app.db.duckdb_client import get_duckdb_client

        return agg_daily_skip_count_sql(get_duckdb_client())

    def _streams_series_from_fact(self, start: date, end: date) -> list[dict[str, Any]]:
        if not self.table_exists("fact_streaming"):
            return []
        ts_col = self._timestamp_column("fact_streaming")
        if not ts_col:
            return []
        dur_col = self._duration_column("fact_streaming")
        dur_expr = f"AVG({dur_col})" if dur_col else "0"
        skip_expr = (
            "SUM(CASE WHEN COALESCE(skipped, FALSE) THEN 1 ELSE 0 END)"
            if self._has_column("fact_streaming", "skipped")
            else "0"
        )
        return self.fetch_all(
            f"""
            SELECT
                CAST({ts_col} AS DATE) AS fecha,
                COUNT(*) AS total_streams,
                COUNT(DISTINCT id_usuario) AS unique_users,
                {skip_expr} AS skip_count,
                {dur_expr} AS avg_duration_ms
            FROM fact_streaming
            WHERE CAST({ts_col} AS DATE) BETWEEN ? AND ?
            GROUP BY 1
            ORDER BY fecha ASC
            """,
            [start, end],
            label="repo_streams_series_fact",
        )

    def get_peak_hours(self, start: date, end: date) -> list[dict[str, Any]]:
        if not self.table_exists("fact_streaming"):
            return []
        ts_col = self._timestamp_column("fact_streaming")
        if not ts_col:
            return []
        hour_col = self._hour_column("fact_streaming")
        hour_expr = (
            f"CAST({hour_col} AS INTEGER)"
            if hour_col
            else f"CAST(EXTRACT(hour FROM {ts_col}) AS INTEGER)"
        )
        return self.fetch_all(
            f"""
            SELECT
                {hour_expr} AS hour_of_day,
                COUNT(*) AS stream_count
            FROM fact_streaming
            WHERE CAST({ts_col} AS DATE) BETWEEN ? AND ?
            GROUP BY 1
            ORDER BY hour_of_day ASC
            """,
            [start, end],
            label="repo_peak_hours",
        )

    def _has_column(self, table: str, column: str) -> bool:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        return column.lower() in {r[0].lower() for r in rows}

    def _timestamp_column(self, table: str) -> str | None:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        cols = {r[0].lower(): r[0] for r in rows}
        for candidate in ("fecha_evento", "played_at", "event_time"):
            if candidate in cols:
                return cols[candidate]
        return None

    def _duration_column(self, table: str) -> str | None:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        cols = {r[0].lower(): r[0] for r in rows}
        for candidate in ("duracion_ms", "duration_ms"):
            if candidate in cols:
                return cols[candidate]
        return None

    def _hour_column(self, table: str) -> str | None:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        cols = {r[0].lower(): r[0] for r in rows}
        if "hour_of_day" in cols:
            return cols["hour_of_day"]
        return None

    def get_trending_artists(self, *, limit: int = 10) -> list[dict[str, Any]]:
        if not self.table_exists("agg_artist_growth"):
            return []
        return self.fetch_all(
            """
            SELECT id_artista, nombre_artista, streams_7d, growth_pct, total_followers
            FROM agg_artist_growth
            ORDER BY growth_pct DESC, streams_7d DESC
            LIMIT ?
            """,
            [limit],
            label="repo_trending_artists",
        )

    def get_genre_trends(self, *, limit: int = 10) -> list[dict[str, Any]]:
        if self.table_exists("agg_genre_trends"):
            return self.fetch_all(
                """
                SELECT id_genero, nombre_genero, streams_7d, trend_pct, avg_popularity
                FROM agg_genre_trends
                ORDER BY streams_7d DESC, trend_pct DESC
                LIMIT ?
                """,
                [limit],
                label="repo_genre_trends",
            )
        if self.table_exists("agg_genero_popularidad"):
            return self.fetch_all(
                """
                SELECT
                    id_genero,
                    nombre_genero,
                    CAST(total_tracks * popularidad_promedio AS INTEGER) AS streams_7d,
                    popularidad_promedio AS trend_pct,
                    popularidad_promedio AS avg_popularity
                FROM agg_genero_popularidad
                ORDER BY popularidad_promedio DESC
                LIMIT ?
                """,
                [limit],
                label="repo_genre_popularity",
            )
        return []

    def get_device_breakdown(self, *, limit: int = 10) -> list[dict[str, Any]]:
        if self.table_exists("agg_platform_usage"):
            return self.fetch_all(
                """
                SELECT platform, device_type, total_streams, share_pct, session_count
                FROM agg_platform_usage
                ORDER BY share_pct DESC
                LIMIT ?
                """,
                [limit],
                label="repo_device_breakdown",
            )
        if self.table_exists("agg_streaming_devices"):
            return self.fetch_all(
                """
                SELECT
                    'unknown' AS platform,
                    device_type,
                    stream_count AS total_streams,
                    share_pct,
                    unique_users AS session_count
                FROM agg_streaming_devices
                ORDER BY share_pct DESC
                LIMIT ?
                """,
                [limit],
                label="repo_streaming_devices",
            )
        return []

    def get_growth_trends(self, *, days: int = 30) -> list[dict[str, Any]]:
        if not self.table_exists("agg_daily_streams"):
            return []
        return self.fetch_all(
            """
            SELECT fecha, total_streams, unique_users
            FROM agg_daily_streams
            ORDER BY fecha DESC
            LIMIT ?
            """,
            [days],
            label="repo_growth_trends",
        )

    def get_latest_daily_totals(self) -> dict[str, Any] | None:
        totals: dict[str, Any] | None = None
        if self.table_exists("agg_daily_streams"):
            totals = self.fetch_one(
                """
                SELECT
                    COALESCE(SUM(total_streams), 0) AS total_streams,
                    COALESCE(MAX(unique_users), 0) AS active_users
                FROM (
                    SELECT total_streams, unique_users
                    FROM agg_daily_streams
                    ORDER BY fecha DESC
                    LIMIT 7
                ) recent
                """,
                label="repo_latest_daily_totals",
            )
        if totals and int(totals.get("total_streams") or 0) > 0:
            return totals
        return self._totals_from_fact() or totals

    def _totals_from_fact(self) -> dict[str, Any] | None:
        if not self.table_exists("fact_streaming"):
            return None
        row = self.fetch_one(
            """
            SELECT
                COUNT(*) AS total_streams,
                COUNT(DISTINCT id_usuario) AS active_users
            FROM fact_streaming
            """,
            label="repo_totals_fact",
        )
        if not row or int(row.get("total_streams") or 0) == 0:
            return None
        return row
