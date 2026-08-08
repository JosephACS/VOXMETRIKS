"""Public visibility rules for catalog tracks linked to editorial publishing."""

from __future__ import annotations

from app.core.database import table_exists


def public_track_visibility_sql(conn) -> str:
    """
    SQL predicate (no params) for rows in ``dim_track dt`` that are publicly
    discoverable.

    Imported catalog tracks (no publishing link) remain visible.
    Tracks linked to submissions are public only when the submission is
    ``published`` and its planned release date (if any) is not in the future.
    Draft / review / approved / scheduled / suspended / withdrawn stay hidden.
    """
    if not table_exists(conn, "app_release_submission") or not table_exists(
        conn, "app_release_submission_track"
    ):
        return "1=1"
    return """
    (
      NOT EXISTS (
        SELECT 1
        FROM app_release_submission_track st
        JOIN app_release_submission s ON s.id = st.submission_id
        WHERE st.warehouse_track_id = dt.id_track
      )
      OR EXISTS (
        SELECT 1
        FROM app_release_submission_track st
        JOIN app_release_submission s ON s.id = st.submission_id
        WHERE st.warehouse_track_id = dt.id_track
          AND s.status = 'published'
          AND (
            s.planned_release_date IS NULL
            OR CAST(s.planned_release_date AS DATE) <= CURRENT_DATE
          )
      )
    )
    """


def is_track_publicly_visible(conn, track_id: int) -> bool:
    """Return True when ``track_id`` passes public visibility rules."""
    if not table_exists(conn, "dim_track"):
        return False
    vis = public_track_visibility_sql(conn)
    row = conn.execute(
        f"SELECT 1 FROM dim_track dt WHERE dt.id_track = ? AND ({vis})",
        [int(track_id)],
    ).fetchone()
    return bool(row)
