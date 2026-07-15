"""Release submission state machine — Spec 031."""

from __future__ import annotations

import os
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.catalog_publishing.domain.errors import (
    InvalidTransitionError,
    SelfApproveError,
)

VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"submitted", "archived", "withdrawn"}),
    "submitted": frozenset({"under_review", "changes_requested", "withdrawn"}),
    "changes_requested": frozenset({"submitted", "withdrawn", "archived"}),
    "under_review": frozenset(
        {"approved", "rejected", "changes_requested", "withdrawn"}
    ),
    "approved": frozenset({"scheduled", "published", "withdrawn"}),
    "scheduled": frozenset({"published", "withdrawn", "suspended"}),
    "published": frozenset({"suspended", "withdrawn"}),
    "suspended": frozenset({"published", "withdrawn", "archived"}),
    "rejected": frozenset({"archived", "draft"}),
    "withdrawn": frozenset({"archived"}),
    "archived": frozenset(),
}

# Reviewer decisions that must not be made by the submission creator.
_SELF_APPROVE_TARGETS = frozenset({"approved", "rejected", "changes_requested"})

_SUB_COLS = (
    "id", "organization_id", "artist_profile_id", "release_type", "title",
    "version", "label_name", "genre", "language", "explicit",
    "planned_release_date", "actual_release_date", "upc", "cover_media_id",
    "status", "created_by", "reviewer_id", "rights_contract_id",
    "catalog_asset_id", "catalog_release_id", "reject_reason", "withdraw_reason",
    "is_demo", "scheduled_at", "published_at", "idempotency_key",
    "created_at", "updated_at",
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _allow_demo_self_approve() -> bool:
    return os.environ.get("ALLOW_DEMO_SELF_APPROVE", "").strip() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _rewrite_submission(
    conn: duckdb.DuckDBPyConnection, row: dict[str, Any]
) -> None:
    """DELETE+INSERT to avoid DuckDB spurious PK errors on UPDATE."""
    sid = int(row["id"])
    conn.execute("DELETE FROM app_release_submission WHERE id = ?", [sid])
    conn.execute(
        f"""
        INSERT INTO app_release_submission
            ({', '.join(_SUB_COLS)})
        VALUES ({', '.join('?' for _ in _SUB_COLS)})
        """,
        [row[c] for c in _SUB_COLS],
    )


def transition(
    conn: duckdb.DuckDBPyConnection,
    submission: dict[str, Any],
    to_status: str,
    *,
    actor_user_id: int,
    reason: Optional[str] = None,
) -> dict[str, Any]:
    """Apply a legal status transition and append history.

    Blocks illegal jumps. Blocks self-approve when creator == actor unless
    ALLOW_DEMO_SELF_APPROVE=1 and submission.is_demo.
    """
    from_status = str(submission.get("status") or "")
    if to_status == from_status:
        raise InvalidTransitionError(
            f"Already in status '{from_status}'"
        )
    allowed = VALID_TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise InvalidTransitionError(
            f"Illegal transition {from_status!r} -> {to_status!r}"
        )

    if to_status in _SELF_APPROVE_TARGETS:
        creator = submission.get("created_by")
        is_demo = bool(submission.get("is_demo"))
        if (
            creator is not None
            and int(creator) == int(actor_user_id)
            and not (_allow_demo_self_approve() and is_demo)
        ):
            raise SelfApproveError(
                "Creator cannot approve or review their own submission"
            )

    now = utc_now()
    sid = int(submission["id"])
    hist_id = _next_id(conn, "app_release_status_history")
    conn.execute(
        """
        INSERT INTO app_release_status_history
            (id, submission_id, from_status, to_status, actor_user_id, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [hist_id, sid, from_status, to_status, actor_user_id, reason, now],
    )

    # Reload latest row then rewrite (DuckDB UPDATE+index quirk)
    fresh = conn.execute(
        f"SELECT {', '.join(_SUB_COLS)} FROM app_release_submission WHERE id = ?",
        [sid],
    ).fetchone()
    row = {c: fresh[i] for i, c in enumerate(_SUB_COLS)}
    row["status"] = to_status
    row["updated_at"] = now
    if to_status == "published":
        row["published_at"] = now
    if to_status == "scheduled" and row.get("scheduled_at") is None:
        row["scheduled_at"] = now
    _rewrite_submission(conn, row)
    return row
