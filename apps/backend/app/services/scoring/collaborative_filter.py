from __future__ import annotations

from app.db.duckdb_client import DuckDBClient
from app.services._warehouse import table_exists
from app.services.scoring._helpers import min_max_scale


class CollaborativeFilter:
    """Simple co-listening filter — device, platform, hour, genre overlap (no ML)."""

    def __init__(self, client: DuckDBClient) -> None:
        self._client = client

    def load_track_scores(self, user_id: int, *, limit_users: int = 40) -> dict[int, float]:
        if not table_exists(self._client, "fact_streaming"):
            return {}

        ts_col = self._timestamp_col()
        cols = self._stream_cols()
        if not ts_col:
            return self._genre_only_scores(user_id)

        overlap_parts: list[str] = []
        if "device_type" in cols:
            overlap_parts.append("fs.device_type = me.device_type")
        if "platform" in cols:
            overlap_parts.append("fs.platform = me.platform")
        overlap_parts.append(
            f"CAST(EXTRACT(hour FROM fs.{ts_col}) AS INTEGER) = me.peak_hour"
        )
        if table_exists(self._client, "dim_track"):
            overlap_parts.append("dt.id_genero IN (SELECT id_genero FROM my_genres)")

        overlap_sql = " OR ".join(f"({p})" for p in overlap_parts) or "FALSE"

        device_sel = (
            """(SELECT device_type FROM fact_streaming WHERE id_usuario = ?
                GROUP BY device_type ORDER BY COUNT(*) DESC LIMIT 1)"""
            if "device_type" in cols
            else "NULL"
        )
        platform_sel = (
            """(SELECT platform FROM fact_streaming WHERE id_usuario = ?
                GROUP BY platform ORDER BY COUNT(*) DESC LIMIT 1)"""
            if "platform" in cols
            else "NULL"
        )

        params: list[int] = []
        me_device = f"{device_sel} AS device_type," if "device_type" in cols else "NULL AS device_type,"
        me_platform = f"{platform_sel} AS platform," if "platform" in cols else "NULL AS platform,"
        if "device_type" in cols:
            params.append(user_id)
        if "platform" in cols:
            params.append(user_id)
        params.append(user_id)  # peak hour

        join_track = (
            "LEFT JOIN dim_track dt ON dt.id_track = fs.id_track"
            if table_exists(self._client, "dim_track")
            else ""
        )
        my_genres_cte = (
            """
            my_genres AS (
                SELECT dt.id_genero, COUNT(*) AS plays
                FROM fact_streaming fs
                INNER JOIN dim_track dt ON dt.id_track = fs.id_track
                WHERE fs.id_usuario = ? AND dt.id_genero IS NOT NULL
                GROUP BY dt.id_genero
            ),
            """
            if table_exists(self._client, "dim_track")
            else ""
        )
        if my_genres_cte:
            params.append(user_id)

        params.extend([user_id, user_id, limit_users])

        sql = f"""
            WITH me AS (
                SELECT
                    {me_device}
                    {me_platform}
                    (SELECT CAST(EXTRACT(hour FROM {ts_col}) AS INTEGER)
                     FROM fact_streaming WHERE id_usuario = ?
                     GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 1) AS peak_hour
            ),
            {my_genres_cte}
            my_tracks AS (
                SELECT DISTINCT id_track FROM fact_streaming WHERE id_usuario = ?
            ),
            similar_users AS (
                SELECT fs.id_usuario, COUNT(*) AS overlap_score
                FROM fact_streaming fs
                CROSS JOIN me
                {join_track}
                WHERE fs.id_usuario != ?
                  AND fs.id_track NOT IN (SELECT id_track FROM my_tracks)
                  AND ({overlap_sql})
                GROUP BY fs.id_usuario
                ORDER BY overlap_score DESC
                LIMIT ?
            ),
            co_listen AS (
                SELECT fs.id_track, COUNT(DISTINCT fs.id_usuario) AS similar_listeners
                FROM fact_streaming fs
                WHERE fs.id_usuario IN (SELECT id_usuario FROM similar_users)
                  AND fs.id_track NOT IN (SELECT id_track FROM my_tracks)
                GROUP BY fs.id_track
            )
            SELECT id_track, similar_listeners FROM co_listen
        """

        rows = self._client.fetch_all(sql, params, label="collab_co_listen_scores")
        if not rows:
            return {}

        max_listeners = max(int(r["similar_listeners"] or 0) for r in rows) or 1
        return {
            int(r["id_track"]): round(
                min_max_scale(float(r["similar_listeners"]), 0, max_listeners),
                4,
            )
            for r in rows
        }

    def _genre_only_scores(self, user_id: int) -> dict[int, float]:
        if not table_exists(self._client, "dim_track"):
            return {}
        rows = self._client.fetch_all(
            """
            WITH my_genres AS (
                SELECT dt.id_genero
                FROM fact_streaming fs
                INNER JOIN dim_track dt ON dt.id_track = fs.id_track
                WHERE fs.id_usuario = ?
                GROUP BY dt.id_genero
            ),
            my_tracks AS (
                SELECT DISTINCT id_track FROM fact_streaming WHERE id_usuario = ?
            )
            SELECT fs.id_track, COUNT(DISTINCT fs.id_usuario) AS similar_listeners
            FROM fact_streaming fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE dt.id_genero IN (SELECT id_genero FROM my_genres)
              AND fs.id_usuario != ?
              AND fs.id_track NOT IN (SELECT id_track FROM my_tracks)
            GROUP BY fs.id_track
            """,
            [user_id, user_id, user_id],
            label="collab_genre_only",
        )
        if not rows:
            return {}
        mx = max(int(r["similar_listeners"] or 0) for r in rows) or 1
        return {
            int(r["id_track"]): round(min_max_scale(float(r["similar_listeners"]), 0, mx), 4)
            for r in rows
        }

    def _stream_cols(self) -> set[str]:
        if not table_exists(self._client, "fact_streaming"):
            return set()
        return {
            r[0].lower()
            for r in self._client.connect().execute("DESCRIBE fact_streaming").fetchall()
        }

    def _timestamp_col(self) -> str | None:
        cols = self._stream_cols()
        for name in ("fecha_evento", "played_at"):
            if name in cols:
                return name
        return None
