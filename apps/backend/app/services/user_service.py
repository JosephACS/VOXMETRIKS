from __future__ import annotations

from typing import Literal, cast

from app.core.database import get_table_columns
from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import UserActivityResponse, UserProfileResponse
from app.services._warehouse import table_exists

logger = get_logger(__name__)


def _segment_sql(events: str, engagement_expr: str) -> str:
    return f"""
WITH user_stats AS (
    SELECT
        fs.id_usuario,
        COUNT(*) AS total_plays,
        ROUND(AVG({engagement_expr}), 2) AS avg_engagement
    FROM {events} fs
    WHERE fs.id_usuario IS NOT NULL
    GROUP BY 1
),
thresholds AS (
    SELECT
        quantile_cont(total_plays, 0.75) AS p75_plays,
        quantile_cont(total_plays, 0.25) AS p25_plays,
        quantile_cont(avg_engagement, 0.75) AS p75_eng
    FROM user_stats
)
SELECT
    us.id_usuario,
    us.total_plays,
    us.avg_engagement,
    CASE
        WHEN us.total_plays >= t.p75_plays OR us.avg_engagement >= t.p75_eng
            THEN 'power_users'
        WHEN us.total_plays >= t.p25_plays
            THEN 'regular_users'
        ELSE 'casual_users'
    END AS segment
FROM user_stats us
CROSS JOIN thresholds t
WHERE us.id_usuario = ?
"""


class UserService:
    """User profiles and activity from Silver/GOLD + warehouse dims."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    def _events_table(self) -> str:
        if table_exists(self._client, "silver_streams"):
            return "silver_streams"
        if table_exists(self._client, "fact_streaming"):
            return "fact_streaming"
        return "silver_streams"

    def _engagement_expr(self, *, for_aggregate: bool = False) -> str:
        events = self._events_table()
        conn = self._client.connect()
        if events == "silver_streams":
            cols = set(get_table_columns(conn, events))
            if "engagement_score" in cols:
                return "COALESCE(fs.engagement_score, 0)"
        return "COALESCE(fs.streams, 1) * COALESCE(fs.duracion_ms, 0) / 1000.0"

    def get_user(self, user_id: int) -> UserProfileResponse | None:
        profile = None
        if table_exists(self._client, "silver_users"):
            profile = self._client.fetch_one(
                """
                SELECT id_usuario, nombre, email, pais, plan
                FROM silver_users
                WHERE id_usuario = ?
                """,
                [user_id],
                label="user_profile_silver",
            )
        if profile is None and table_exists(self._client, "dim_usuario"):
            conn = self._client.connect()
            cols = set(get_table_columns(conn, "dim_usuario"))
            if "nombre" in cols:
                name_col = "nombre"
            elif "nombre_usuario" in cols:
                name_col = "nombre_usuario"
            else:
                name_col = "CAST(id_usuario AS VARCHAR)"
            select_cols = [f"{name_col} AS nombre", "id_usuario"]
            for optional in ("email", "pais", "plan"):
                if optional in cols:
                    select_cols.append(optional)
            profile = self._client.fetch_one(
                f"""
                SELECT {", ".join(select_cols)}
                FROM dim_usuario
                WHERE id_usuario = ?
                """,
                [user_id],
                label="user_profile_dim",
            )
        if profile is None:
            return None

        events = self._events_table()
        engagement = 0.0
        segment = "unknown"

        if table_exists(self._client, events):
            eng_row = self._client.fetch_one(
                f"""
                SELECT ROUND(AVG({self._engagement_expr()}), 2) AS engagement_score
                FROM {events} fs
                WHERE fs.id_usuario = ?
                """,
                [user_id],
                label="user_engagement_score",
            )
            if eng_row:
                engagement = float(eng_row.get("engagement_score") or 0)

            seg_row = self._client.fetch_one(
                _segment_sql(events, self._engagement_expr()),
                [user_id],
                label="user_segment",
            )
            if seg_row and seg_row.get("segment"):
                segment = str(seg_row["segment"])

        return UserProfileResponse(
            id_usuario=int(profile["id_usuario"]),
            nombre=str(profile.get("nombre") or ""),
            email=profile.get("email"),
            pais=profile.get("pais"),
            plan=profile.get("plan"),
            engagement_score=engagement,
            segment=cast(
                Literal["power_users", "regular_users", "casual_users", "unknown"],
                segment,
            ),
        )

    def get_user_activity(self, user_id: int) -> UserActivityResponse | None:
        if not self.get_user(user_id):
            return None

        plays = skips = sessions = 0
        likes = 0

        if table_exists(self._client, "fact_streaming"):
            cols = {
                r[0]
                for r in self._client.connect().execute("DESCRIBE fact_streaming").fetchall()
            }
            id_col = "id_usuario" if "id_usuario" in cols else None
            if id_col:
                skip_expr = (
                    "SUM(CASE WHEN COALESCE(skipped, FALSE) THEN 1 ELSE 0 END)"
                    if "skipped" in cols
                    else "0"
                )
                session_parts = [c for c in ("session_id", "id_streaming", "id_stream") if c in cols]
                if session_parts:
                    session_expr = f"COUNT(DISTINCT COALESCE({', '.join(session_parts)}))"
                elif "played_at" in cols:
                    session_expr = "COUNT(DISTINCT played_at)"
                else:
                    session_expr = "COUNT(*)"
                row = self._client.fetch_one(
                    f"""
                    SELECT
                        COUNT(*) AS plays,
                        {skip_expr} AS skips,
                        {session_expr} AS sessions
                    FROM fact_streaming
                    WHERE {id_col} = ?
                    """,
                    [user_id],
                    label="user_activity_streams",
                )
                if row:
                    plays = int(row.get("plays") or 0)
                    skips = int(row.get("skips") or 0)
                    sessions = int(row.get("sessions") or 0)

        if table_exists(self._client, "app_favorite"):
            likes = int(
                self._client.fetch_scalar(
                    "SELECT COUNT(*) FROM app_favorite WHERE user_id = ?",
                    [user_id],
                    label="user_activity_likes",
                )
                or 0
            )

        return UserActivityResponse(
            id_usuario=user_id,
            plays=plays,
            skips=skips,
            likes=likes,
            sessions=sessions,
        )
