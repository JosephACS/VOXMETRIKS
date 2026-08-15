"""Organization Journey read model + completion (Spec 053).

Composes Organizations, module-access, Subscriptions and Checkout 052.
Does not grant entitlements or rewrite billing/subscription truth.
GET paths are side-effect-free (no ensure_* / DDL).
"""

from __future__ import annotations

from typing import Any, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.organizations.application.module_access import get_org_subscription_snapshot
from app.packages.organizations.domain.errors import (
    NotFoundError,
    PermissionDenied,
    ValidationError,
)
from app.packages.organizations.infrastructure.org_profile_catalogs import (
    INVITATION_SAFE_ROLE_CODES,
    MEMBERSHIP_STATUS_LABELS,
)
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)


def ensure_onboarding_row(conn: duckdb.DuckDBPyConnection, organization_id: int) -> None:
    """Create in_progress onboarding metadata if missing (write path only)."""
    exists = conn.execute(
        "SELECT 1 FROM app_organization_onboarding WHERE organization_id = ?",
        [organization_id],
    ).fetchone()
    if exists:
        return
    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_organization_onboarding
            (organization_id, status, team_step_skipped_at, completed_by, completed_at,
             created_at, updated_at)
        VALUES (?, 'in_progress', NULL, NULL, NULL, ?, ?)
        """,
        [organization_id, now, now],
    )


def _table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE lower(table_name) = lower(?)
        LIMIT 1
        """,
        [name],
    ).fetchone()
    return bool(row)


def _read_onboarding(conn: duckdb.DuckDBPyConnection, organization_id: int) -> dict[str, Any]:
    if not _table_exists(conn, "app_organization_onboarding"):
        return {
            "organization_id": organization_id,
            "status": "in_progress",
            "team_step_skipped_at": None,
            "completed_by": None,
            "completed_at": None,
        }
    row = conn.execute(
        """
        SELECT organization_id, status, team_step_skipped_at, completed_by, completed_at
        FROM app_organization_onboarding WHERE organization_id = ?
        """,
        [organization_id],
    ).fetchone()
    if not row:
        return {
            "organization_id": organization_id,
            "status": "in_progress",
            "team_step_skipped_at": None,
            "completed_by": None,
            "completed_at": None,
        }
    return {
        "organization_id": int(row[0]),
        "status": str(row[1]),
        "team_step_skipped_at": row[2],
        "completed_by": int(row[3]) if row[3] is not None else None,
        "completed_at": row[4],
    }


def _open_checkout(conn: duckdb.DuckDBPyConnection, organization_id: int) -> Optional[dict[str, Any]]:
    if not _table_exists(conn, "app_subscription_checkout_session"):
        return None
    row = conn.execute(
        """
        SELECT id, status, plan_code, amount, currency, failure_code
        FROM app_subscription_checkout_session
        WHERE organization_id = ?
          AND status IN ('draft', 'awaiting_method', 'ready', 'failed', 'processing')
        ORDER BY id DESC LIMIT 1
        """,
        [organization_id],
    ).fetchone()
    if not row:
        return None
    return {
        "id": int(row[0]),
        "status": str(row[1]),
        "plan_code": str(row[2]),
        "amount": float(row[3]) if row[3] is not None else None,
        "currency": str(row[4]) if row[4] else None,
        "failure_code": row[5],
        "checkout_url": (
            f"/subscriptions/checkout?organization_id={organization_id}"
            f"&checkout_id={int(row[0])}"
        ),
    }


def _has_succeeded_checkout(conn: duckdb.DuckDBPyConnection, organization_id: int) -> bool:
    if not _table_exists(conn, "app_subscription_checkout_session"):
        return False
    row = conn.execute(
        """
        SELECT 1 FROM app_subscription_checkout_session
        WHERE organization_id = ? AND status = 'succeeded'
        ORDER BY id DESC LIMIT 1
        """,
        [organization_id],
    ).fetchone()
    return bool(row)


def _subscription_summary(conn: duckdb.DuckDBPyConnection, organization_id: int) -> dict[str, Any]:
    snap = get_org_subscription_snapshot(conn, organization_id)
    plan_name = None
    trial = False
    status = snap.get("status")
    if snap.get("subscription_id") and _table_exists(conn, "app_subscription"):
        plan_row = conn.execute(
            """
            SELECT p.display_name, s.status, s.trial_ends_at
            FROM app_subscription s
            JOIN app_plan p ON p.id = s.plan_id
            WHERE s.id = ? AND s.organization_id = ?
            """,
            [snap["subscription_id"], organization_id],
        ).fetchone()
        if plan_row:
            plan_name = str(plan_row[0])
            status = str(plan_row[1])
            trial = status == "trialing" or plan_row[2] is not None
    return {
        "status": status,
        "plan_name": plan_name,
        "trial": bool(trial),
        "subscription_id": snap.get("subscription_id"),
    }


def _team_summary(conn: duckdb.DuckDBPyConnection, organization_id: int) -> dict[str, int]:
    active = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM app_organization_member
            WHERE organization_id = ? AND status = 'active'
            """,
            [organization_id],
        ).fetchone()[0]
    )
    pending = 0
    if _table_exists(conn, "app_organization_invitation"):
        pending = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM app_organization_invitation
                WHERE organization_id = ? AND status = 'pending'
                """,
                [organization_id],
            ).fetchone()[0]
        )
    return {"active_members": active, "pending_invitations": pending}


def _role_codes_for_member(conn: duckdb.DuckDBPyConnection, member_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT br.code
        FROM app_member_role mr
        JOIN app_business_role br ON br.id = mr.role_id
        WHERE mr.member_id = ? AND mr.status = 'active' AND br.is_active = TRUE
        """,
        [member_id],
    ).fetchall()
    return [str(r[0]) for r in rows]


def _capabilities(
    *,
    permissions: set[str],
    access_tier: str,
    operational_plan: bool,
    checkout: Optional[dict[str, Any]],
    onboarding_status: str,
    can_setup: bool,
) -> dict[str, bool]:
    # Parity with Spec 052 routes: subscription.create only (not billing.manage).
    can_subscribe = "subscription.create" in permissions
    resume = bool(
        checkout
        and str(checkout.get("status"))
        in {"draft", "awaiting_method", "ready", "failed", "processing"}
        and can_subscribe
    )
    choose = (
        can_setup
        and can_subscribe
        and not operational_plan
        and not resume
        and access_tier in {"onboarding", "recovery", "operational"}
    )
    return {
        "update_profile": "organization.update" in permissions,
        "choose_plan": choose,
        "resume_checkout": resume,
        "invite_team": "member.invite" in permissions,
        "view_members": "member.view" in permissions,
        # Historical onboarding completion never unlocks the hub.
        "enter_workspace": access_tier == "operational",
        "complete_journey": can_setup
        and operational_plan
        and onboarding_status != "completed"
        and access_tier == "operational",
    }


def _derive_next_action(
    *,
    org_status: str,
    can_setup: bool,
    caps: dict[str, bool],
    operational_plan: bool,
    checkout: Optional[dict[str, Any]],
    onboarding: dict[str, Any],
    profile_ok: bool,
    access_tier: str,
) -> str:
    if org_status in {"closed", "suspended_by_platform"}:
        return "organization_unavailable"

    onboarding_done = onboarding.get("status") == "completed"

    # Completed metadata never unlocks the hub by itself.
    if onboarding_done and access_tier != "operational":
        if not can_setup:
            return "wait_for_owner"
        if caps.get("resume_checkout"):
            return "resume_checkout"
        if caps.get("choose_plan"):
            return "choose_plan"
        return "wait_for_owner"

    if access_tier == "operational" and onboarding_done:
        return "enter_workspace"

    if not can_setup:
        if access_tier == "operational":
            return "enter_workspace"
        return "wait_for_owner"

    if not profile_ok:
        return "review_profile"
    if checkout and str(checkout.get("status")) == "processing":
        return "await_payment"
    if caps.get("resume_checkout"):
        return "resume_checkout"
    if not operational_plan:
        return "choose_plan"
    if caps.get("invite_team") and onboarding.get("team_step_skipped_at") is None:
        return "invite_team"
    if caps.get("complete_journey"):
        return "complete"
    if access_tier == "operational":
        return "enter_workspace"
    return "wait_for_owner"


def get_journey(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    permissions: set[str],
) -> dict[str, Any]:
    """Side-effect-free journey read model (no DDL / ensure_*)."""
    if "organization.view" not in permissions:
        raise PermissionDenied("Missing organization.view")

    org = OrganizationRepository(conn).get_by_id(organization_id)
    member = MembershipRepository(conn).get_by_org_and_user(organization_id, actor_user_id)
    if member is None or member.status != "active":
        raise NotFoundError("organization not found")

    onboarding = _read_onboarding(conn, organization_id)
    snap = get_org_subscription_snapshot(conn, organization_id)
    access_tier = str(snap.get("tier") or "onboarding")
    subscription = _subscription_summary(conn, organization_id)
    checkout = _open_checkout(conn, organization_id)
    team = _team_summary(conn, organization_id)

    sub_status = str(subscription.get("status") or snap.get("status") or "")
    operational_plan = sub_status in {"trialing", "active"} and access_tier == "operational"

    actor_roles = set(_role_codes_for_member(conn, member.id))
    can_setup = bool(
        actor_roles & {"owner", "administrator"}
        or "subscription.create" in permissions
        or "organization.update" in permissions
    )
    profile_ok = bool(
        (org.display_name or "").strip() and (org.organization_type or "").strip()
    )

    caps = _capabilities(
        permissions=permissions,
        access_tier=access_tier,
        operational_plan=operational_plan,
        checkout=checkout,
        onboarding_status=str(onboarding["status"]),
        can_setup=can_setup,
    )
    next_action = _derive_next_action(
        org_status=str(org.status),
        can_setup=can_setup,
        caps=caps,
        operational_plan=operational_plan,
        checkout=checkout,
        onboarding=onboarding,
        profile_ok=profile_ok,
        access_tier=access_tier,
    )

    completed: list[str] = ["organization"]
    if profile_ok:
        completed.append("profile")
    if operational_plan or sub_status in {"trialing", "active", "past_due"}:
        completed.append("plan")
    if _has_succeeded_checkout(conn, organization_id):
        completed.append("checkout")
    if onboarding.get("team_step_skipped_at") is not None or team["pending_invitations"] > 0:
        completed.append("team")
    if onboarding.get("status") == "completed":
        completed.append("completed")

    allowed: list[str] = ["profile"]
    if caps["choose_plan"] or caps["resume_checkout"] or operational_plan:
        allowed.append("plan")
    if caps["resume_checkout"]:
        allowed.append("checkout")
    if caps["invite_team"] or caps["view_members"]:
        allowed.append("team")
    if caps["enter_workspace"]:
        allowed.append("hub")

    return {
        "organization": {
            "id": org.id,
            "display_name": org.display_name,
            "slug": org.slug,
            "organization_type": org.organization_type,
            "legal_name": org.legal_name,
            "country_code": org.country_code,
            "timezone": org.timezone,
            "default_currency": org.default_currency,
            "status": org.status,
        },
        "membership": {
            "id": member.id,
            "status": member.status,
            "status_label": MEMBERSHIP_STATUS_LABELS.get(member.status, member.status),
        },
        "access_tier": access_tier,
        "completed_steps": completed,
        "next_action": next_action,
        "capabilities": caps,
        "subscription": {
            "status": subscription.get("status"),
            "plan_name": subscription.get("plan_name"),
            "trial": subscription.get("trial"),
        },
        "checkout": checkout,
        "team": team,
        "allowed_destinations": allowed,
        "onboarding_status": onboarding["status"],
        "journey_url": "/organizations/onboarding",
    }


def complete_journey(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    permissions: set[str],
    idempotency_key: str,
    team_step_skipped: bool = False,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    if not idempotency_key or not idempotency_key.strip():
        raise ValidationError("idempotency_key is required")

    with transactional(conn):
        ensure_onboarding_row(conn, organization_id)
        journey = get_journey(
            conn,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            permissions=permissions,
        )
        if journey["onboarding_status"] == "completed":
            return journey

        if not journey["capabilities"].get("complete_journey"):
            raise ValidationError("journey_prerequisite_missing")

        snap = get_org_subscription_snapshot(conn, organization_id)
        if snap.get("status") not in {"trialing", "active"}:
            raise ValidationError("journey_prerequisite_missing")
        if str(snap.get("tier") or "") != "operational":
            raise ValidationError("journey_prerequisite_missing")

        now = utc_now()
        if team_step_skipped:
            conn.execute(
                """
                UPDATE app_organization_onboarding
                SET team_step_skipped_at = COALESCE(team_step_skipped_at, ?),
                    updated_at = ?
                WHERE organization_id = ?
                """,
                [now, now, organization_id],
            )
        conn.execute(
            """
            UPDATE app_organization_onboarding
            SET status = 'completed', completed_by = ?, completed_at = ?, updated_at = ?
            WHERE organization_id = ?
            """,
            [actor_user_id, now, now, organization_id],
        )
        AuditRepository(conn).append(
            action="organization.journey_completed",
            target_type="organization",
            source="api",
            result="success",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            target_id=str(organization_id),
            new_values={
                "idempotency_key": idempotency_key.strip(),
                "team_step_skipped": bool(team_step_skipped),
            },
            request_id=request_id,
        )

    return get_journey(
        conn,
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        permissions=permissions,
    )


def skip_team_step(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    permissions: set[str],
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    if "member.invite" not in permissions and "organization.update" not in permissions:
        raise PermissionDenied("Missing permission")
    now = utc_now()
    with transactional(conn):
        ensure_onboarding_row(conn, organization_id)
        conn.execute(
            """
            UPDATE app_organization_onboarding
            SET team_step_skipped_at = COALESCE(team_step_skipped_at, ?), updated_at = ?
            WHERE organization_id = ?
            """,
            [now, now, organization_id],
        )
        AuditRepository(conn).append(
            action="organization.journey_team_skipped",
            target_type="organization",
            source="api",
            result="success",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            target_id=str(organization_id),
            request_id=request_id,
        )
    return get_journey(
        conn,
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        permissions=permissions,
    )


def list_invitation_roles(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    permissions: set[str],
) -> list[dict[str, str]]:
    """Read-only role catalog (no DDL)."""
    if "member.invite" not in permissions and "role.view" not in permissions:
        raise PermissionDenied("Missing permission")
    member = MembershipRepository(conn).get_by_org_and_user(organization_id, actor_user_id)
    if member is None or member.status != "active":
        raise NotFoundError("organization not found")

    rows = conn.execute(
        """
        SELECT code, display_name, description
        FROM app_business_role
        WHERE is_active = TRUE AND scope = 'organization'
        ORDER BY display_name ASC
        """
    ).fetchall()
    actor_roles = set(_role_codes_for_member(conn, member.id))
    can_assign_elevated = "owner" in actor_roles or "administrator" in actor_roles

    items: list[dict[str, str]] = []
    for code, label, description in rows:
        c = str(code)
        if c not in INVITATION_SAFE_ROLE_CODES:
            continue
        if c == "administrator" and not can_assign_elevated:
            continue
        items.append(
            {
                "code": c,
                "label": str(label),
                "description": str(description or ""),
            }
        )
    return items


def enrich_member_presentation(
    conn: duckdb.DuckDBPyConnection,
    members: list[Any],
) -> list[dict[str, Any]]:
    """Additive safe presentation for member list responses."""
    out: list[dict[str, Any]] = []
    for m in members:
        mid = int(m.id)
        uid = int(m.user_id)
        user_row = conn.execute(
            """
            SELECT COALESCE(NULLIF(username, ''), split_part(email, '@', 1)), email
            FROM app_user WHERE id = ?
            """,
            [uid],
        ).fetchone()
        display = str(user_row[0]) if user_row else "Miembro"
        email = str(user_row[1]) if user_row else None
        roles = []
        for code in _role_codes_for_member(conn, mid):
            label_row = conn.execute(
                "SELECT display_name FROM app_business_role WHERE code = ?",
                [code],
            ).fetchone()
            roles.append(
                {
                    "code": code,
                    "label": str(label_row[0]) if label_row else code,
                }
            )
        out.append(
            {
                "id": mid,
                "organization_id": int(m.organization_id),
                "user_id": uid,
                "status": m.status,
                "status_label": MEMBERSHIP_STATUS_LABELS.get(m.status, m.status),
                "joined_at": m.joined_at,
                "suspended_at": m.suspended_at,
                "left_at": m.left_at,
                "removed_at": m.removed_at,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
                "user": {"display_name": display, "email": email},
                "roles": roles,
            }
        )
    return out


def assert_invitation_role_assignable(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    role_code: str,
) -> str:
    code = (role_code or "").strip().lower()
    member = MembershipRepository(conn).get_by_org_and_user(organization_id, actor_user_id)
    if member is None:
        raise NotFoundError("organization not found")
    actor_roles = set(_role_codes_for_member(conn, member.id))
    if code == "owner":
        if "owner" not in actor_roles:
            raise PermissionDenied("Cannot assign owner")
        return code
    if code not in INVITATION_SAFE_ROLE_CODES:
        raise ValidationError("invalid_catalog_value")
    if code == "administrator" and not (actor_roles & {"owner", "administrator"}):
        raise PermissionDenied("Cannot assign administrator")
    return code
