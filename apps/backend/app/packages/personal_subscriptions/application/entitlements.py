"""Personal entitlement enforcement — Spec 029.

Backend is the source of truth; frontend messages are UX only.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import duckdb

from app.packages.personal_subscriptions.domain.errors import EntitlementLimitError
from app.packages.personal_subscriptions.infrastructure.schema import (
    ensure_personal_subscription_tables,
)


def _active_subscription_row(
    conn: duckdb.DuckDBPyConnection, user_id: int
) -> Optional[tuple]:
    """Return active personal sub for user (own or household member entitlement)."""
    # Prefer own active/premium subscription
    row = conn.execute(
        """
        SELECT s.id, s.plan_id, s.status, s.access_state, s.grace_until, p.code, p.is_free
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status IN ('active', 'past_due', 'processing')
        ORDER BY CASE WHEN p.is_free THEN 1 ELSE 0 END, s.id DESC
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if row:
        return row

    # Household member: inherit owner's premium plan features
    member = conn.execute(
        """
        SELECT hm.household_id
        FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not member:
        return None
    hh_id = int(member[0])
    owner = conn.execute(
        "SELECT owner_user_id FROM household WHERE id = ?", [hh_id]
    ).fetchone()
    if not owner:
        return None
    return conn.execute(
        """
        SELECT s.id, s.plan_id, s.status, s.access_state, s.grace_until, p.code, p.is_free
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status IN ('active', 'past_due')
          AND p.is_free = FALSE
        ORDER BY s.id DESC LIMIT 1
        """,
        [int(owner[0])],
    ).fetchone()


def get_feature_limit(
    conn: duckdb.DuckDBPyConnection, user_id: int, feature_code: str
) -> Optional[int]:
    """Return limit (None = unlimited) or raise if feature disabled.

    If no subscription, Free defaults are used after ensuring Free exists.
    """
    ensure_personal_subscription_tables(conn)
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
    )

    ensure_free_subscription(conn, user_id)
    row = _active_subscription_row(conn, user_id)
    if not row:
        # Hard Free defaults
        defaults = {"playlists": 3, "favorites": 50, "history_recent": 25, "household_members": 1}
        return defaults.get(feature_code)

    plan_id = int(row[1])
    status = row[2]
    access = row[3]
    # past_due with grace still keeps premium features until grace ends / downgrade
    if status == "past_due" and access == "limited":
        feat = conn.execute(
            """
            SELECT limit_value, enabled FROM personal_plan_feature
            WHERE plan_id = (SELECT id FROM personal_plan WHERE code = 'personal_free')
              AND feature_code = ?
            """,
            [feature_code],
        ).fetchone()
        if feat and feat[1]:
            return int(feat[0]) if feat[0] is not None else None
        return {"playlists": 3, "favorites": 50}.get(feature_code)

    feat = conn.execute(
        """
        SELECT limit_value, enabled FROM personal_plan_feature
        WHERE plan_id = ? AND feature_code = ?
        """,
        [plan_id, feature_code],
    ).fetchone()
    if not feat:
        # aliases
        if feature_code == "history_recent":
            full = conn.execute(
                """
                SELECT 1 FROM personal_plan_feature
                WHERE plan_id = ? AND feature_code = 'history_full' AND enabled = TRUE
                """,
                [plan_id],
            ).fetchone()
            if full:
                return None
        return None
    if not feat[1]:
        return 0
    return int(feat[0]) if feat[0] is not None else None


def effective_limits(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
    )

    ensure_free_subscription(conn, user_id)
    row = _active_subscription_row(conn, user_id)
    plan_code = "personal_free"
    status = "active"
    if row:
        plan_code = str(row[5])
        status = str(row[2])
    features = conn.execute(
        """
        SELECT feature_code, limit_value, enabled
        FROM personal_plan_feature
        WHERE plan_id = (SELECT id FROM personal_plan WHERE code = ?)
        """,
        [plan_code],
    ).fetchall()
    return {
        "plan_code": plan_code,
        "status": status,
        "owner_type": "user",
        "features": {
            str(f[0]): {"limit": (int(f[1]) if f[1] is not None else None), "enabled": bool(f[2])}
            for f in features
        },
    }


def assert_can_create_playlist(conn: duckdb.DuckDBPyConnection, user_id: int) -> None:
    limit = get_feature_limit(conn, user_id, "playlists")
    if limit is None:
        return
    count = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_playlist WHERE user_id = ?", [user_id]
        ).fetchone()[0]
    )
    if count >= limit:
        raise EntitlementLimitError("playlists", limit)


def assert_can_add_favorite(conn: duckdb.DuckDBPyConnection, user_id: int) -> None:
    limit = get_feature_limit(conn, user_id, "favorites")
    if limit is None:
        return
    # Existing favorite is OK (idempotent add)
    count = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_favorite WHERE user_id = ?", [user_id]
        ).fetchone()[0]
    )
    if count >= limit:
        raise EntitlementLimitError("favorites", limit)


def history_cap(conn: duckdb.DuckDBPyConnection, user_id: int, requested: int) -> int:
    """Cap history page size for Free (recent) vs Premium (full)."""
    full = get_feature_limit(conn, user_id, "history_full")
    # None with feature present or alias check
    row = _active_subscription_row(conn, user_id)
    if row and not bool(row[6]):  # not is_free
        return min(max(1, requested), 200)
    recent = get_feature_limit(conn, user_id, "history_recent")
    cap = int(recent) if recent is not None else 25
    return min(max(1, requested), cap)


def has_advanced_queue(conn: duckdb.DuckDBPyConnection, user_id: int) -> bool:
    row = _active_subscription_row(conn, user_id)
    if not row or bool(row[6]):
        return False
    feat = conn.execute(
        """
        SELECT 1 FROM personal_plan_feature
        WHERE plan_id = ? AND feature_code = 'queue_advanced' AND enabled = TRUE
        """,
        [int(row[1])],
    ).fetchone()
    return feat is not None
