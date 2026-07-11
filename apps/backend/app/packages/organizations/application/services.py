"""Shared helpers for use cases: user lookup, permission checks, audit."""

from __future__ import annotations

from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.enums import (
    MembershipStatus,
    OrganizationStatus,
)
from app.packages.organizations.domain.errors import (
    MembershipNotFound,
    OrganizationNotFound,
    OrganizationNotOperational,
    PermissionDenied,
    UserNotFound,
)
from app.packages.organizations.domain.rules import normalize_email
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)


def require_user(conn: duckdb.DuckDBPyConnection, user_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT id, username, email, role
        FROM app_user WHERE id = ?
        """,
        [user_id],
    ).fetchone()
    if not row:
        raise UserNotFound(f"user id={user_id}")
    return {
        "id": int(row[0]),
        "username": str(row[1]),
        "email": normalize_email(str(row[2])),
        "role": str(row[3] or "user").lower(),
    }


def get_organization_or_raise(
    orgs: OrganizationRepository, organization_id: int
):
    try:
        return orgs.get_by_id(organization_id)
    except Exception as exc:
        from app.packages.organizations.domain.errors import NotFoundError

        if isinstance(exc, NotFoundError):
            raise OrganizationNotFound(str(exc)) from exc
        raise


def require_active_membership(
    members: MembershipRepository,
    *,
    organization_id: int,
    user_id: int,
):
    membership = members.get_by_org_and_user(organization_id, user_id)
    if membership is None:
        raise MembershipNotFound(
            f"no membership org={organization_id} user={user_id}"
        )
    if membership.status != MembershipStatus.ACTIVE.value:
        raise PermissionDenied(
            f"membership status={membership.status} is not active"
        )
    return membership


def require_permission(
    auth: AuthorizationRepository,
    *,
    member_id: int,
    permission_code: str,
) -> None:
    if not auth.member_has_permission(member_id, permission_code):
        raise PermissionDenied(f"missing permission {permission_code}")


def require_org_active_for_mutations(org) -> None:
    if org.status != OrganizationStatus.ACTIVE.value:
        raise OrganizationNotOperational(
            f"organization status={org.status} does not allow mutations"
        )


def audit(
    audits: AuditRepository,
    *,
    action: str,
    target_type: str,
    result: str,
    organization_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    actor_platform_role: Optional[str] = None,
    target_id: Optional[str] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
    source: str = "organizations.use_case",
):
    return audits.append(
        action=action,
        target_type=target_type,
        source=source,
        result=result,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_platform_role=actor_platform_role,
        target_id=target_id,
        previous_values=previous_values,
        new_values=new_values,
        reason=reason,
        request_id=request_id,
    )


def now():
    return utc_now()
