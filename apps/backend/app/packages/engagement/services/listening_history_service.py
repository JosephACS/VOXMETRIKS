"""Personal listening history — app_listening_history (account-scoped, not warehouse)."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.catalog.services.display_text import clean_catalog_rows
from app.packages.engagement.services.app_storage import ensure_app_tables
from app.packages.personal_subscriptions.application.entitlements import history_cap

# Backend source of truth for counted listens.
LISTEN_THRESHOLD_MS = 30_000
SHORT_TRACK_MS = 60_000


def meets_listen_threshold(
    listened_ms: int,
    duration_ms: Optional[int] = None,
) -> bool:
    listened = max(0, int(listened_ms or 0))
    if listened >= LISTEN_THRESHOLD_MS:
        return True
    dur = int(duration_ms or 0)
    if 0 < dur < SHORT_TRACK_MS and listened >= int(dur * 0.5):
        return True
    return False


def _track_duration_ms(conn: duckdb.DuckDBPyConnection, track_id: int) -> Optional[int]:
    try:
        row = conn.execute(
            "SELECT duration_ms FROM dim_track WHERE id_track = ?", [int(track_id)]
        ).fetchone()
        if row and row[0] is not None:
            return int(row[0])
    except Exception:
        return None
    return None


def ensure_listening_history_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Always create the table (works even when schema_ready short-circuits ensure_app_tables)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_listening_history (
            id            INTEGER PRIMARY KEY,
            user_id       INTEGER NOT NULL,
            track_id      INTEGER NOT NULL,
            event_key     VARCHAR NOT NULL UNIQUE,
            played_at     TIMESTAMP NOT NULL,
            progress_ms   INTEGER NOT NULL DEFAULT 0,
            listened_ms   INTEGER NOT NULL DEFAULT 0,
            completed     BOOLEAN NOT NULL DEFAULT FALSE,
            source        VARCHAR,
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_listening_history_user_played
        ON app_listening_history(user_id, played_at)
        """
    )


def _next_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM app_listening_history"
    ).fetchone()
    return int(row[0])


def _track_exists(conn: duckdb.DuckDBPyConnection, track_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM dim_track WHERE id_track = ?", [int(track_id)]
    ).fetchone()
    return bool(row)


def _row_to_item(r: tuple) -> Dict[str, Any]:
    item = {
        "id": int(r[0]),
        "user_id": int(r[1]),
        "id_track": int(r[2]),
        "event_key": r[3],
        "played_at": str(r[4]) if r[4] else None,
        "viewed_at": str(r[4]) if r[4] else None,  # FE HistoryEntry compat
        "progress_ms": int(r[5] or 0),
        "listened_ms": int(r[6] or 0),
        "completed": bool(r[7]),
        "source": r[8],
        "created_at": str(r[9]) if r[9] else None,
        "updated_at": str(r[10]) if r[10] else None,
        "nombre_track": r[11],
        "nombre_artista": r[12],
        "duration_ms": int(r[13]) if r[13] is not None else None,
        "id_artista": int(r[14]) if r[14] is not None else None,
        "popularity": int(r[15]) if r[15] is not None else None,
    }
    return item


_SELECT = """
    SELECT
        h.id, h.user_id, h.track_id, h.event_key, h.played_at,
        h.progress_ms, h.listened_ms, h.completed, h.source,
        h.created_at, h.updated_at,
        dt.nombre_track, da.nombre_artista, dt.duration_ms,
        dt.id_artista, dt.popularity
    FROM app_listening_history h
    JOIN dim_track dt ON dt.id_track = h.track_id
    LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
"""


def start_playback(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    track_id: int,
    *,
    event_key: Optional[str] = None,
    source: Optional[str] = None,
    progress_ms: Optional[int] = None,
    listened_ms: Optional[int] = None,
) -> Dict[str, Any]:
    tid = int(track_id)
    key = (event_key or "").strip() or f"play:{user_id}:{tid}:{secrets.token_hex(8)}"
    now = utc_now()
    init_progress = max(0, int(progress_ms or 0))
    init_listened = max(0, int(listened_ms or 0))

    # Single serialized unit under transactional(): schema ensure, track check,
    # event_key lookup, idempotent update / id+insert, and result read.
    # No network I/O inside this context.
    with transactional(conn):
        ensure_app_tables(conn)
        ensure_listening_history_table(conn)
        if not _track_exists(conn, tid):
            raise ValueError("track_not_found")

        existing = conn.execute(
            "SELECT id, progress_ms, listened_ms FROM app_listening_history WHERE event_key = ? AND user_id = ?",
            [key, user_id],
        ).fetchone()
        if existing:
            # Idempotent retry: bump metrics monotonically so a late /start still
            # retains the listen that qualified the event.
            eid = int(existing[0])
            new_progress = max(init_progress, int(existing[1] or 0))
            new_listened = max(init_listened, int(existing[2] or 0))
            if new_progress != int(existing[1] or 0) or new_listened != int(existing[2] or 0):
                conn.execute(
                    """
                    UPDATE app_listening_history
                    SET progress_ms = ?, listened_ms = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    [new_progress, new_listened, now, eid, user_id],
                )
            return get_entry(conn, user_id, eid) or {
                "id": eid,
                "event_key": key,
            }

        new_id = _next_id(conn)
        conn.execute(
            """
            INSERT INTO app_listening_history (
                id, user_id, track_id, event_key, played_at,
                progress_ms, listened_ms, completed, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, ?, ?, ?)
            """,
            [
                new_id,
                user_id,
                tid,
                key,
                now,
                init_progress,
                init_listened,
                source or "player",
                now,
                now,
            ],
        )
        return get_entry(conn, user_id, new_id) or {
            "id": new_id,
            "event_key": key,
            "id_track": tid,
        }


def update_progress(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    event_key: str,
    *,
    progress_ms: Optional[int] = None,
    listened_ms: Optional[int] = None,
    completed: Optional[bool] = None,
) -> Dict[str, Any]:
    ensure_listening_history_table(conn)
    key = (event_key or "").strip()
    if not key:
        raise ValueError("event_key_required")
    row = conn.execute(
        "SELECT id, progress_ms, listened_ms, completed, track_id FROM app_listening_history WHERE event_key = ? AND user_id = ?",
        [key, user_id],
    ).fetchone()
    if not row:
        raise LookupError("not_found")

    new_progress = int(progress_ms) if progress_ms is not None else int(row[1] or 0)
    new_listened = int(listened_ms) if listened_ms is not None else int(row[2] or 0)
    # Monotonic progress/listened
    new_progress = max(new_progress, int(row[1] or 0))
    new_listened = max(new_listened, int(row[2] or 0))
    duration_ms = _track_duration_ms(conn, int(row[4]))
    # Never mark completed unless the listen threshold is met (backend rule).
    want_completed = bool(row[3]) or bool(completed)
    if want_completed and not meets_listen_threshold(new_listened, duration_ms):
        want_completed = bool(row[3])
    new_completed = want_completed
    now = utc_now()
    conn.execute(
        """
        UPDATE app_listening_history
        SET progress_ms = ?, listened_ms = ?, completed = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        [new_progress, new_listened, new_completed, now, int(row[0]), user_id],
    )
    entry = get_entry(conn, user_id, int(row[0])) or {"id": int(row[0]), "event_key": key}
    entry["qualified"] = meets_listen_threshold(new_listened, duration_ms)
    return entry


def complete_playback(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    event_key: str,
    *,
    progress_ms: Optional[int] = None,
    listened_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Mark complete using explicit listened_ms only.

    ``progress_ms`` is playback position and must never be inferred as
    ``listened_ms``. When ``listened_ms`` is omitted, the previously stored
    value is kept (via ``update_progress``).
    """
    return update_progress(
        conn,
        user_id,
        event_key,
        progress_ms=progress_ms,
        listened_ms=listened_ms,
        completed=True,
    )


def get_entry(
    conn: duckdb.DuckDBPyConnection, user_id: int, entry_id: int
) -> Optional[Dict[str, Any]]:
    ensure_listening_history_table(conn)
    row = conn.execute(
        _SELECT + " WHERE h.id = ? AND h.user_id = ?",
        [entry_id, user_id],
    ).fetchone()
    if not row:
        return None
    return clean_catalog_rows([_row_to_item(row)])[0]


def list_history(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    page: int = 1,
    limit: int = 30,
) -> Dict[str, Any]:
    ensure_app_tables(conn)
    ensure_listening_history_table(conn)
    page = max(1, int(page))
    limit = history_cap(conn, user_id, int(limit))
    offset = (page - 1) * limit
    total = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_listening_history WHERE user_id = ?",
            [user_id],
        ).fetchone()[0]
    )
    rows = conn.execute(
        _SELECT
        + """
        WHERE h.user_id = ?
        ORDER BY h.played_at DESC, h.id DESC
        LIMIT ? OFFSET ?
        """,
        [user_id, limit, offset],
    ).fetchall()
    items = clean_catalog_rows([_row_to_item(r) for r in rows])
    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "has_more": offset + len(items) < total,
    }


def list_recent(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, limit: int = 8
) -> List[Dict[str, Any]]:
    """Latest play events (capped) for continue-listening."""
    ensure_listening_history_table(conn)
    limit = history_cap(conn, user_id, int(limit))
    rows = conn.execute(
        _SELECT
        + """
        WHERE h.user_id = ?
        ORDER BY h.played_at DESC, h.id DESC
        LIMIT ?
        """,
        [user_id, limit],
    ).fetchall()
    # Dedupe by track keeping first (latest) occurrence
    seen: set[int] = set()
    items: List[Dict[str, Any]] = []
    for r in rows:
        tid = int(r[2])
        if tid in seen:
            continue
        seen.add(tid)
        items.append(_row_to_item(r))
        if len(items) >= limit:
            break
    return clean_catalog_rows(items)


def delete_entry(
    conn: duckdb.DuckDBPyConnection, user_id: int, entry_id: int
) -> bool:
    ensure_listening_history_table(conn)
    before = conn.execute(
        "SELECT 1 FROM app_listening_history WHERE id = ? AND user_id = ?",
        [entry_id, user_id],
    ).fetchone()
    if not before:
        return False
    conn.execute(
        "DELETE FROM app_listening_history WHERE id = ? AND user_id = ?",
        [entry_id, user_id],
    )
    return True


def clear_history(conn: duckdb.DuckDBPyConnection, user_id: int) -> int:
    ensure_listening_history_table(conn)
    count = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_listening_history WHERE user_id = ?",
            [user_id],
        ).fetchone()[0]
    )
    conn.execute(
        "DELETE FROM app_listening_history WHERE user_id = ?", [user_id]
    )
    return count


def migrate_local_entries(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Idempotent import of localStorage history for the authenticated user only."""
    ensure_listening_history_table(conn)
    imported = 0
    skipped = 0
    invalid = 0
    for raw in entries or []:
        try:
            tid = int(raw.get("id_track") or raw.get("track_id") or 0)
            if tid <= 0 or not _track_exists(conn, tid):
                invalid += 1
                continue
            viewed = raw.get("viewed_at") or raw.get("played_at") or ""
            # Stable key: same local entry won't re-import
            key = f"migrate:{user_id}:{tid}:{str(viewed)[:32]}"
            exists = conn.execute(
                "SELECT 1 FROM app_listening_history WHERE event_key = ?",
                [key],
            ).fetchone()
            if exists:
                skipped += 1
                continue
            now = utc_now()
            played_at = now
            if viewed:
                try:
                    # Accept ISO strings; fall back to now
                    played_at = datetime.fromisoformat(
                        str(viewed).replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except Exception:  # noqa: BLE001
                    played_at = now
            new_id = _next_id(conn)
            conn.execute(
                """
                INSERT INTO app_listening_history (
                    id, user_id, track_id, event_key, played_at,
                    progress_ms, listened_ms, completed, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 0, 0, FALSE, 'migrate', ?, ?)
                """,
                [new_id, user_id, tid, key, played_at, now, now],
            )
            imported += 1
        except Exception:  # noqa: BLE001
            invalid += 1
    return {
        "imported": imported,
        "skipped": skipped,
        "invalid": invalid,
        "ok": True,
    }


def user_history_track_ids(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, limit: int = 50
) -> List[int]:
    """Track ids from real personal history for recommendations (no warehouse mix)."""
    ensure_listening_history_table(conn)
    limit = history_cap(conn, user_id, limit)
    rows = conn.execute(
        """
        SELECT track_id FROM app_listening_history
        WHERE user_id = ?
        ORDER BY played_at DESC
        LIMIT ?
        """,
        [user_id, limit],
    ).fetchall()
    return [int(r[0]) for r in rows]
