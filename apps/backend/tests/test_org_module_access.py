"""Organization module access tiers — membership + subscription gate."""

from __future__ import annotations

import duckdb
import pytest
from fastapi import HTTPException

from app.packages.organizations.application.module_access import (
    assert_org_module_access,
    get_org_subscription_snapshot,
    resolve_org_access_tier,
    tier_allows,
)


def test_resolve_tiers():
    assert resolve_org_access_tier(None, None) == "onboarding"
    assert resolve_org_access_tier("active", "full") == "operational"
    assert resolve_org_access_tier("trialing", "full") == "operational"
    assert resolve_org_access_tier("active", "limited") == "recovery"
    assert resolve_org_access_tier("past_due", "limited") == "recovery"
    assert resolve_org_access_tier("canceled", "blocked") == "recovery"


def test_tier_allows_matrix():
    assert tier_allows("onboarding", "onboarding")
    assert not tier_allows("onboarding", "operational")
    assert tier_allows("recovery", "recovery")
    assert not tier_allows("recovery", "operational")
    assert tier_allows("operational", "operational")
    assert tier_allows("operational", "recovery")


def test_snapshot_empty_and_assert_blocks():
    conn = duckdb.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE app_subscription (
          id INTEGER,
          organization_id INTEGER,
          status VARCHAR,
          access_state VARCHAR
        )
        """
    )
    snap = get_org_subscription_snapshot(conn, organization_id=42)
    assert snap["has_subscription"] is False
    assert snap["tier"] == "onboarding"

    with pytest.raises(HTTPException) as ei:
        assert_org_module_access(conn, 42, module_kind="operational")
    assert ei.value.status_code == 403
    assert ei.value.detail["code"] == "subscription_required"

    conn.execute(
        "INSERT INTO app_subscription VALUES (1, 42, 'active', 'full')"
    )
    snap2 = get_org_subscription_snapshot(conn, organization_id=42)
    assert snap2["tier"] == "operational"
    assert assert_org_module_access(conn, 42, module_kind="operational")["tier"] == "operational"

    conn.execute("UPDATE app_subscription SET status = 'past_due', access_state = 'limited'")
    with pytest.raises(HTTPException) as ei2:
        assert_org_module_access(conn, 42, module_kind="operational")
    assert ei2.value.detail["code"] == "subscription_inactive"
    assert assert_org_module_access(conn, 42, module_kind="recovery")["tier"] == "recovery"
    conn.close()
