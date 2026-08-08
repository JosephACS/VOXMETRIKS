"""Organization module access gate — membership + subscription tier.

UI and API must agree: operational modules need active/trialing with full access;
recovery modules remain available when past_due / limited / canceled / expired.
"""

from __future__ import annotations

from typing import Literal, Optional

import duckdb
from fastapi import HTTPException

OrgModuleKind = Literal["onboarding", "recovery", "operational"]

_ACTIVE_LIKE = frozenset({"trialing", "active"})
_RECOVERY_STATUSES = frozenset({"past_due", "canceled", "expired", "suspended"})


def get_org_subscription_snapshot(
    conn: duckdb.DuckDBPyConnection, organization_id: int
) -> dict:
    """Return the most relevant subscription row for gating (prefer active-like)."""
    row = conn.execute(
        """
        SELECT id, status, access_state
        FROM app_subscription
        WHERE organization_id = ?
        ORDER BY
          CASE status
            WHEN 'active' THEN 0
            WHEN 'trialing' THEN 1
            WHEN 'past_due' THEN 2
            WHEN 'canceled' THEN 3
            WHEN 'expired' THEN 4
            ELSE 5
          END,
          id DESC
        LIMIT 1
        """,
        [organization_id],
    ).fetchone()
    if not row:
        return {
            "has_subscription": False,
            "subscription_id": None,
            "status": None,
            "access_state": None,
            "tier": "onboarding",
        }
    status = str(row[1] or "").lower()
    access = str(row[2] or "full").lower()
    tier = resolve_org_access_tier(status, access)
    return {
        "has_subscription": True,
        "subscription_id": int(row[0]),
        "status": status,
        "access_state": access,
        "tier": tier,
    }


def resolve_org_access_tier(status: Optional[str], access_state: Optional[str]) -> str:
    if not status:
        return "onboarding"
    st = status.lower()
    access = (access_state or "full").lower()
    if st in _ACTIVE_LIKE:
        if access in ("blocked", "limited"):
            return "recovery"
        return "operational"
    if st in _RECOVERY_STATUSES:
        return "recovery"
    return "onboarding"


def tier_allows(tier: str, module_kind: OrgModuleKind) -> bool:
    if module_kind in ("onboarding",):
        return tier in ("onboarding", "recovery", "operational")
    if module_kind == "recovery":
        return tier in ("recovery", "operational")
    if module_kind == "operational":
        return tier == "operational"
    return False


def assert_org_module_access(
    conn: duckdb.DuckDBPyConnection,
    organization_id: int,
    *,
    module_kind: OrgModuleKind = "operational",
) -> dict:
    """Raise 403 when subscription tier does not allow the module kind."""
    snap = get_org_subscription_snapshot(conn, organization_id)
    if tier_allows(str(snap["tier"]), module_kind):
        return snap
    if snap["tier"] == "onboarding":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "subscription_required",
                "message": (
                    "Your organization is created. Choose a business plan or start a "
                    "free trial to activate management tools."
                ),
            },
        )
    raise HTTPException(
        status_code=403,
        detail={
            "code": "subscription_inactive",
            "message": (
                "This feature is temporarily blocked because the business "
                "subscription is not active."
            ),
        },
    )
