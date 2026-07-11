from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import duckdb

from app.core.database import get_table_columns, using_write_conn
from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import (
    LiveSessionStatsResponse,
    StreamActionRequest,
    StreamActionResponse,
    StreamEndRequest,
    StreamEndResponse,
    StreamStartRequest,
    StreamStartResponse,
)
from app.services._warehouse import table_exists

logger = get_logger(__name__)

EVENT_START = "STREAM_START"
EVENT_END = "STREAM_END"
EVENT_SKIP = "STREAM_SKIP"
EVENT_PAUSE = "STREAM_PAUSE"
EVENT_RESUME = "STREAM_RESUME"

FACT_SESSIONS_DDL = """
CREATE TABLE IF NOT EXISTS fact_stream_sessions (
    id_session      INTEGER PRIMARY KEY,
    id_usuario      INTEGER NOT NULL,
    device_type     VARCHAR NOT NULL,
    platform        VARCHAR NOT NULL,
    session_start   TIMESTAMP NOT NULL,
    session_end     TIMESTAMP,
    tracks_played   INTEGER DEFAULT 0,
    total_ms        INTEGER DEFAULT 0,
    skips           INTEGER DEFAULT 0
)
"""

FACT_USER_ACTIVITY_DDL = """
CREATE TABLE IF NOT EXISTS fact_user_activity (
    id_activity     INTEGER PRIMARY KEY,
    id_usuario      INTEGER NOT NULL,
    id_track        INTEGER,
    id_tiempo       INTEGER,
    action_type     VARCHAR NOT NULL,
    device_type     VARCHAR DEFAULT 'mobile',
    duration_ms     INTEGER DEFAULT 0,
    fecha_evento    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


@dataclass
class _StreamRow:
    stream_id: int
    user_id: int
    track_id: int
    session_id: int | None
    device_type: str | None
    platform: str | None
    duration_ms: int
    completed: bool
    skipped: bool


class StreamingService:
    """Event-driven streaming engine — real-time writes to warehouse fact tables."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    # ── Public event API ──────────────────────────────────────────────────────

    def start_stream(self, payload: StreamStartRequest) -> StreamStartResponse:
        started_at = datetime.now(timezone.utc)
        with using_write_conn() as conn:
            self._ensure_tables(conn)
            self._validate_track(conn, payload.track_id)

            session_id = self._get_or_create_session(
                conn,
                user_id=payload.user_id,
                device_type=payload.device_type,
                platform=payload.platform,
                started_at=started_at,
            )
            stream_id = self._insert_streaming_event(
                conn,
                user_id=payload.user_id,
                track_id=payload.track_id,
                session_id=session_id,
                device_type=payload.device_type,
                platform=payload.platform,
                started_at=started_at,
            )
            self._log_activity(
                conn,
                user_id=payload.user_id,
                track_id=payload.track_id,
                action_type=EVENT_START,
                device_type=payload.device_type,
                duration_ms=0,
                at=started_at,
            )

        logger.info(
            "event=%s stream_id=%s session_id=%s user_id=%s track_id=%s",
            EVENT_START,
            stream_id,
            session_id,
            payload.user_id,
            payload.track_id,
        )
        return StreamStartResponse(
            stream_id=stream_id,
            session_id=session_id,
            user_id=payload.user_id,
            track_id=payload.track_id,
            event_type=EVENT_START,
            started_at=started_at,
            device_type=payload.device_type,
            platform=payload.platform,
        )

    def end_stream(self, payload: StreamEndRequest) -> StreamEndResponse:
        ended_at = datetime.now(timezone.utc)
        with using_write_conn() as conn:
            self._ensure_tables(conn)
            row = self._load_stream(conn, payload.stream_id)
            track_duration = self._track_duration_ms(conn, row.track_id)
            engagement = self._compute_engagement(
                payload.duration_ms,
                track_duration,
                payload.completed,
                payload.skipped,
            )
            self._update_streaming_row(
                conn,
                stream_id=payload.stream_id,
                duration_ms=payload.duration_ms,
                completed=payload.completed,
                skipped=payload.skipped,
                engagement=engagement,
            )
            if row.session_id:
                self._update_session(
                    conn,
                    session_id=row.session_id,
                    duration_delta=payload.duration_ms,
                    skipped=payload.skipped,
                    track_completed=True,
                    ended_at=ended_at,
                )
            self._log_activity(
                conn,
                user_id=row.user_id,
                track_id=row.track_id,
                action_type=EVENT_END,
                device_type=row.device_type or "mobile",
                duration_ms=payload.duration_ms,
                at=ended_at,
            )

        logger.info(
            "event=%s stream_id=%s duration_ms=%s engagement=%.3f",
            EVENT_END,
            payload.stream_id,
            payload.duration_ms,
            engagement,
        )
        return StreamEndResponse(
            stream_id=payload.stream_id,
            session_id=row.session_id,
            event_type=EVENT_END,
            duration_ms=payload.duration_ms,
            completed=payload.completed,
            skipped=payload.skipped,
            engagement_score=engagement,
            ended_at=ended_at,
        )

    def skip_track(self, payload: StreamActionRequest) -> StreamActionResponse:
        return self._stream_action(payload, event_type=EVENT_SKIP, force_skipped=True)

    def pause_stream(self, payload: StreamActionRequest) -> StreamActionResponse:
        return self._stream_action(payload, event_type=EVENT_PAUSE)

    def resume_stream(self, payload: StreamActionRequest) -> StreamActionResponse:
        return self._stream_action(payload, event_type=EVENT_RESUME)

    def get_live_session_stats(self, user_id: int) -> LiveSessionStatsResponse:
        if not table_exists(self._client, "fact_stream_sessions"):
            return LiveSessionStatsResponse(
                user_id=user_id,
                active=False,
                session_duration_ms=0,
                tracks_played=0,
                skip_ratio=0.0,
                current_engagement=0.0,
            )

        session = self._client.fetch_one(
            """
            SELECT
                id_session,
                device_type,
                platform,
                session_start,
                tracks_played,
                total_ms,
                skips
            FROM fact_stream_sessions
            WHERE id_usuario = ?
              AND session_end IS NULL
            ORDER BY session_start DESC
            LIMIT 1
            """,
            [user_id],
            label="live_session_lookup",
        )
        if not session:
            return LiveSessionStatsResponse(
                user_id=user_id,
                active=False,
                session_duration_ms=0,
                tracks_played=0,
                skip_ratio=0.0,
                current_engagement=0.0,
            )

        session_id = int(session["id_session"])
        tracks = int(session.get("tracks_played") or 0)
        skips = int(session.get("skips") or 0)
        total_ms = int(session.get("total_ms") or 0)
        skip_ratio = round(skips / tracks, 4) if tracks > 0 else 0.0

        engagement = 0.0
        if table_exists(self._client, "fact_streaming"):
            eng_row = self._client.fetch_one(
                """
                SELECT ROUND(AVG(
                    LEAST(COALESCE(fs.duracion_ms, 0) * 1.0 / 180000.0, 1.0) * 0.5
                    + CASE WHEN COALESCE(fs.completado, FALSE) THEN 0.3 ELSE 0 END
                    - CASE WHEN COALESCE(fs.skipped, FALSE) THEN 0.5 ELSE 0 END
                ), 4) AS avg_engagement
                FROM fact_streaming fs
                WHERE fs.session_id = ?
                """,
                [session_id],
                label="live_session_engagement",
            )
            if eng_row:
                engagement = float(eng_row.get("avg_engagement") or 0)

        start = session.get("session_start")
        if isinstance(start, datetime):
            elapsed = int((datetime.now(timezone.utc) - start.replace(tzinfo=timezone.utc)).total_seconds() * 1000)
            session_duration_ms = max(total_ms, elapsed)
        else:
            session_duration_ms = total_ms

        return LiveSessionStatsResponse(
            user_id=user_id,
            session_id=session_id,
            active=True,
            session_duration_ms=session_duration_ms,
            tracks_played=tracks,
            skip_ratio=skip_ratio,
            current_engagement=engagement,
            device_type=session.get("device_type"),
            platform=session.get("platform"),
        )

    # ── Internal event handler ──────────────────────────────────────────────────

    def _stream_action(
        self,
        payload: StreamActionRequest,
        *,
        event_type: str,
        force_skipped: bool = False,
    ) -> StreamActionResponse:
        at = datetime.now(timezone.utc)
        with using_write_conn() as conn:
            self._ensure_tables(conn)
            row = self._load_stream(conn, payload.stream_id)
            duration_ms = payload.duration_ms if payload.duration_ms is not None else row.duration_ms
            track_duration = self._track_duration_ms(conn, row.track_id)
            skipped = force_skipped or row.skipped
            completed = False if force_skipped else row.completed
            engagement = self._compute_engagement(duration_ms, track_duration, completed, skipped)

            if force_skipped:
                self._update_streaming_row(
                    conn,
                    stream_id=payload.stream_id,
                    duration_ms=duration_ms,
                    completed=False,
                    skipped=True,
                    engagement=engagement,
                )
                if row.session_id:
                    self._update_session(
                        conn,
                        session_id=row.session_id,
                        duration_delta=duration_ms,
                        skipped=True,
                        track_completed=True,
                        ended_at=at,
                    )

            self._log_activity(
                conn,
                user_id=row.user_id,
                track_id=row.track_id,
                action_type=event_type,
                device_type=row.device_type or "mobile",
                duration_ms=duration_ms,
                at=at,
            )

        logger.info("event=%s stream_id=%s session_id=%s", event_type, payload.stream_id, row.session_id)
        return StreamActionResponse(
            stream_id=payload.stream_id,
            session_id=row.session_id,
            event_type=event_type,
            engagement_score=engagement if force_skipped else None,
            timestamp=at,
        )

    # ── Warehouse helpers ───────────────────────────────────────────────────────

    def _ensure_tables(self, conn: duckdb.DuckDBPyConnection) -> None:
        tables = {r[0].lower() for r in conn.execute("SHOW TABLES").fetchall()}
        if "fact_streaming" not in tables:
            raise RuntimeError("fact_streaming table not available")
        conn.execute(FACT_SESSIONS_DDL)
        conn.execute(FACT_USER_ACTIVITY_DDL)

    @staticmethod
    def _validate_track(conn: duckdb.DuckDBPyConnection, track_id: int) -> None:
        exists = conn.execute(
            "SELECT 1 FROM dim_track WHERE id_track = ? LIMIT 1",
            [track_id],
        ).fetchone()
        if not exists:
            raise ValueError(f"Track {track_id} not found")

    @staticmethod
    def _track_duration_ms(conn: duckdb.DuckDBPyConnection, track_id: int) -> int:
        cols = set(get_table_columns(conn, "dim_track"))
        duration_col = "duration_ms" if "duration_ms" in cols else "duracion_ms"
        if duration_col not in cols:
            return 180_000
        row = conn.execute(
            f"SELECT COALESCE({duration_col}, 180000) FROM dim_track WHERE id_track = ?",
            [track_id],
        ).fetchone()
        return int(row[0]) if row else 180_000

    @staticmethod
    def _compute_engagement(
        duration_ms: int,
        track_duration_ms: int,
        completed: bool,
        skipped: bool,
    ) -> float:
        ratio = min(1.0, duration_ms / track_duration_ms) if track_duration_ms > 0 else 0.0
        score = (ratio * 0.5) + (0.3 if completed else 0.0) - (0.5 if skipped else 0.0)
        return round(max(-0.5, min(1.0, score)), 4)

    def _pk_column(self, conn: duckdb.DuckDBPyConnection) -> str:
        cols = get_table_columns(conn, "fact_streaming")
        if "id_streaming" in cols:
            return "id_streaming"
        if "id_stream" in cols:
            return "id_stream"
        raise RuntimeError("fact_streaming has no known primary key column")

    def _get_or_create_session(
        self,
        conn: duckdb.DuckDBPyConnection,
        *,
        user_id: int,
        device_type: str,
        platform: str,
        started_at: datetime,
    ) -> int:
        existing = conn.execute(
            """
            SELECT id_session FROM fact_stream_sessions
            WHERE id_usuario = ?
              AND session_end IS NULL
              AND device_type = ?
              AND platform = ?
            ORDER BY session_start DESC
            LIMIT 1
            """,
            [user_id, device_type, platform],
        ).fetchone()
        if existing:
            return int(existing[0])

        new_id = conn.execute(
            "SELECT COALESCE(MAX(id_session), 0) + 1 FROM fact_stream_sessions"
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO fact_stream_sessions (
                id_session, id_usuario, device_type, platform,
                session_start, tracks_played, total_ms, skips
            ) VALUES (?, ?, ?, ?, ?, 0, 0, 0)
            """,
            [int(new_id), user_id, device_type, platform, started_at],
        )
        return int(new_id)

    def _insert_streaming_event(
        self,
        conn: duckdb.DuckDBPyConnection,
        *,
        user_id: int,
        track_id: int,
        session_id: int,
        device_type: str,
        platform: str,
        started_at: datetime,
    ) -> int:
        pk = self._pk_column(conn)
        cols = set(get_table_columns(conn, "fact_streaming"))
        new_id = conn.execute(f"SELECT COALESCE(MAX({pk}), 0) + 1 FROM fact_streaming").fetchone()[0]

        values: dict[str, Any] = {pk: int(new_id)}
        field_map = {
            "id_usuario": user_id,
            "id_track": track_id,
            "streams": 1,
            "duracion_ms": 0,
            "duration_ms": 0,
            "completado": False,
            "skipped": False,
            "device_type": device_type,
            "platform": platform,
            "fecha_evento": started_at,
            "played_at": started_at,
            "session_id": session_id,
            "hour_of_day": started_at.hour,
        }
        for col, val in field_map.items():
            if col in cols:
                values[col] = val

        col_names = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        conn.execute(
            f"INSERT INTO fact_streaming ({col_names}) VALUES ({placeholders})",
            list(values.values()),
        )
        return int(new_id)

    def _load_stream(self, conn: duckdb.DuckDBPyConnection, stream_id: int) -> _StreamRow:
        pk = self._pk_column(conn)
        cols = set(get_table_columns(conn, "fact_streaming"))
        row = conn.execute(
            f"SELECT * FROM fact_streaming WHERE {pk} = ?",
            [stream_id],
        ).fetchone()
        if not row:
            raise ValueError(f"Stream {stream_id} not found")

        col_list = get_table_columns(conn, "fact_streaming")
        data = dict(zip(col_list, row))
        duration_col = "duracion_ms" if "duracion_ms" in cols else "duration_ms"
        return _StreamRow(
            stream_id=stream_id,
            user_id=int(data.get("id_usuario") or 0),
            track_id=int(data.get("id_track") or 0),
            session_id=int(data["session_id"]) if data.get("session_id") is not None else None,
            device_type=data.get("device_type"),
            platform=data.get("platform"),
            duration_ms=int(data.get(duration_col) or 0),
            completed=bool(data.get("completado", False)),
            skipped=bool(data.get("skipped", False)),
        )

    def _update_streaming_row(
        self,
        conn: duckdb.DuckDBPyConnection,
        *,
        stream_id: int,
        duration_ms: int,
        completed: bool,
        skipped: bool,
        engagement: float,
    ) -> None:
        pk = self._pk_column(conn)
        cols = set(get_table_columns(conn, "fact_streaming"))
        updates: list[str] = []
        params: list[Any] = []

        duration_col = "duracion_ms" if "duracion_ms" in cols else "duration_ms"
        if duration_col in cols:
            updates.append(f"{duration_col} = ?")
            params.append(duration_ms)
        if "completado" in cols:
            updates.append("completado = ?")
            params.append(completed)
        if "skipped" in cols:
            updates.append("skipped = ?")
            params.append(skipped)
        if "engagement_score" in cols:
            updates.append("engagement_score = ?")
            params.append(engagement)

        if not updates:
            raise RuntimeError("fact_streaming has no updatable columns")

        params.append(stream_id)
        conn.execute(
            f"UPDATE fact_streaming SET {', '.join(updates)} WHERE {pk} = ?",
            params,
        )

    def _update_session(
        self,
        conn: duckdb.DuckDBPyConnection,
        *,
        session_id: int,
        duration_delta: int,
        skipped: bool,
        track_completed: bool,
        ended_at: datetime | None = None,
    ) -> None:
        conn.execute(
            """
            UPDATE fact_stream_sessions
            SET
                tracks_played = tracks_played + ?,
                total_ms = total_ms + ?,
                skips = skips + ?
            WHERE id_session = ?
            """,
            [1 if track_completed else 0, duration_delta, 1 if skipped else 0, session_id],
        )

    def _log_activity(
        self,
        conn: duckdb.DuckDBPyConnection,
        *,
        user_id: int,
        track_id: int,
        action_type: str,
        device_type: str,
        duration_ms: int,
        at: datetime,
    ) -> None:
        new_id = int(
            conn.execute("SELECT COALESCE(MAX(id_activity), 0) + 1 FROM fact_user_activity").fetchone()[0]
        )
        cols = set(get_table_columns(conn, "fact_user_activity"))
        row: dict[str, Any] = {
            "id_activity": new_id,
            "id_usuario": user_id,
            "id_track": track_id,
            "action_type": action_type,
            "device_type": device_type,
            "duration_ms": duration_ms,
            "fecha_evento": at,
        }
        if "id_tiempo" in cols:
            row["id_tiempo"] = None
        insert_cols = [k for k in row if k in cols]
        placeholders = ", ".join("?" for _ in insert_cols)
        conn.execute(
            f"INSERT INTO fact_user_activity ({', '.join(insert_cols)}) VALUES ({placeholders})",
            [row[k] for k in insert_cols],
        )
