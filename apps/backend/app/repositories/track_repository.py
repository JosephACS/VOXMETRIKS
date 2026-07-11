from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.sql_loader import load_sql


class TrackRepository(BaseRepository):
    """Track catalog + recommendation scores."""

    def _has_column(self, table: str, column: str) -> bool:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        return column.lower() in {r[0].lower() for r in rows}

    def get_top_tracks(self, *, limit: int = 20) -> list[dict[str, Any]]:
        if self.table_exists("agg_tracks_populares"):
            try:
                use_agg_only = self._has_column("agg_tracks_populares", "total_streams")
                sql_file = "top_tracks_agg" if use_agg_only else "top_tracks"
                rows = self.fetch_all(
                    load_sql(sql_file),
                    [limit],
                    label="repo_top_tracks",
                )
                if rows:
                    return rows
            except Exception:
                pass
        return self._top_tracks_from_catalog(limit=limit)

    def _top_tracks_from_catalog(self, *, limit: int) -> list[dict[str, Any]]:
        if not self.table_exists("dim_track"):
            return []
        track_cols = {
            r[0].lower()
            for r in self.client.connect().execute("DESCRIBE dim_track").fetchall()
        }
        energy_sql = "dt.energy AS energy" if "energy" in track_cols else "CAST(NULL AS DOUBLE) AS energy"
        dance_sql = (
            "dt.danceability AS danceability"
            if "danceability" in track_cols
            else "CAST(NULL AS DOUBLE) AS danceability"
        )
        has_streams = self.table_exists("fact_streaming")
        stream_join = (
            """
            LEFT JOIN (
                SELECT id_track, COUNT(*) AS total_streams
                FROM fact_streaming
                GROUP BY id_track
            ) fs ON fs.id_track = dt.id_track
            """
            if has_streams
            else ""
        )
        stream_col = "COALESCE(fs.total_streams, 0)" if has_streams else "0"
        return self.fetch_all(
            f"""
            SELECT
                dt.id_track,
                dt.nombre_track,
                COALESCE(da.nombre_artista, '—') AS nombre_artista,
                dg.nombre_genero,
                COALESCE(dt.popularity, 0) AS popularity,
                {energy_sql},
                {dance_sql},
                {stream_col} AS total_streams
            FROM dim_track dt
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
            {stream_join}
            WHERE dt.spotify_track_id IS NULL OR dt.spotify_track_id NOT LIKE 'syn_%'
            ORDER BY {stream_col} DESC, dt.popularity DESC NULLS LAST
            LIMIT ?
            """,
            [limit],
            label="repo_top_tracks_catalog",
        )

    def get_recommendations_for_user(self, user_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        if not self.table_exists("agg_recommendation_scores"):
            return []
        return self.fetch_all(
            load_sql("user_recommendations"),
            [user_id, user_id, limit],
            label="repo_user_recommendations",
        )
