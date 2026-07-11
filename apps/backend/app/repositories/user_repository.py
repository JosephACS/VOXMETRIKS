from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """User dimension + activity aggregates."""

    def user_exists(self, user_id: int) -> bool:
        for table, col in (("dim_usuario", "id_usuario"), ("agg_user_activity", "id_usuario")):
            if self.table_exists(table):
                found = self.fetch_scalar(
                    f"SELECT COUNT(*) FROM {table} WHERE {col} = ?",
                    [user_id],
                    label=f"repo_user_exists_{table}",
                )
                if found and int(found) > 0:
                    return True
        if self.table_exists("fact_streaming"):
            found = self.fetch_scalar(
                "SELECT COUNT(*) FROM fact_streaming WHERE id_usuario = ?",
                [user_id],
                label="repo_user_exists_streams",
            )
            return bool(found and int(found) > 0)
        return False

    def get_user_activity(self, user_id: int) -> dict[str, Any] | None:
        if self.table_exists("agg_user_activity"):
            row = self.fetch_one(
                """
                SELECT id_usuario, total_plays, total_skips, total_likes, engagement_score
                FROM agg_user_activity
                WHERE id_usuario = ?
                """,
                [user_id],
                label="repo_user_activity_agg",
            )
            if row:
                return row

        if not self.table_exists("fact_streaming"):
            return None

        skip_expr = (
            "SUM(CASE WHEN COALESCE(skipped, FALSE) THEN 1 ELSE 0 END)"
            if self._has_column("fact_streaming", "skipped")
            else "0"
        )
        return self.fetch_one(
            f"""
            SELECT
                id_usuario,
                COUNT(*) AS total_plays,
                {skip_expr} AS total_skips,
                0 AS total_likes,
                ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT CAST(fecha_evento AS DATE)), 0), 2)
                    AS engagement_score
            FROM fact_streaming
            WHERE id_usuario = ?
            GROUP BY id_usuario
            """,
            [user_id],
            label="repo_user_activity_fact",
        )

    def get_favorites_count(self, user_id: int) -> int:
        if self.table_exists("app_favorite"):
            return int(
                self.fetch_scalar(
                    "SELECT COUNT(*) FROM app_favorite WHERE user_id = ?",
                    [user_id],
                    label="repo_user_favorites_app",
                )
                or 0
            )
        if self.table_exists("fact_favorites"):
            return int(
                self.fetch_scalar(
                    "SELECT COUNT(*) FROM fact_favorites WHERE id_usuario = ?",
                    [user_id],
                    label="repo_user_favorites_fact",
                )
                or 0
            )
        return 0

    def get_engagement_segment(self, user_id: int) -> str | None:
        if not self.table_exists("agg_user_engagement"):
            return None
        activity = self.get_user_activity(user_id)
        if not activity:
            return None
        plays = int(activity.get("total_plays") or 0)
        row = self.fetch_one(
            """
            SELECT segment FROM agg_user_engagement
            ORDER BY avg_plays DESC
            LIMIT 1
            """,
            label="repo_user_segment_proxy",
        )
        if plays >= 40:
            return "power_users"
        if plays >= 15:
            return "regular_users"
        if plays > 0:
            return "casual_users"
        return row.get("segment") if row else None

    def _has_column(self, table: str, column: str) -> bool:
        rows = self.client.connect().execute(f"DESCRIBE {table}").fetchall()
        return column.lower() in {r[0].lower() for r in rows}
