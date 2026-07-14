"""FastAPI dependencies for organization context and permissions."""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header, Request

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.organizations.application.context import OrganizationContext
from app.packages.organizations.application.dto import ActorContext
from app.packages.organizations.application.services import require_user
from app.packages.organizations.domain.enums import MembershipStatus, OrganizationStatus
from app.packages.organizations.domain.errors import (
    MembershipNotFound,
    OrganizationNotFound,
    PermissionDenied,
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
from app.packages.organizations.infrastructure.repositories.preference_repository import (
    PreferenceRepository,
)
from app.packages.organizations.presentation.error_mapping import http_error, raise_domain_http


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def get_actor(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    request_id: str = Depends(request_id_header),
) -> ActorContext:
    user = require_user(conn, user_id)
    return ActorContext(
        user_id=user_id,
        platform_role=user.get("role"),
        request_id=request_id,
    )


def _load_context_for_org(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    organization_id: int,
    source: str,
    platform_role: Optional[str],
    request_id: Optional[str],
    require_active_org: bool,
) -> OrganizationContext:
    orgs = OrganizationRepository(conn)
    members = MembershipRepository(conn)
    auth = AuthorizationRepository(conn)
    prefs = PreferenceRepository(conn)

    try:
        org = orgs.get_by_id(organization_id)
    except Exception:
        raise http_error(404, "Not found", code="not_found")

    membership = members.get_by_org_and_user(organization_id, user_id)
    if membership is None:
        raise http_error(404, "Not found", code="not_found")

    if membership.status != MembershipStatus.ACTIVE.value:
        # access_revoked — clear stale preference
        pref = prefs.get_for_user(user_id)
        if pref and pref.active_organization_id == organization_id:
            prefs.clear_active_organization(user_id, updated_by=user_id)
        raise http_error(403, "Membership not active", code="access_revoked")

    if require_active_org and org.status != OrganizationStatus.ACTIVE.value:
        if org.status == OrganizationStatus.CLOSED.value:
            pref = prefs.get_for_user(user_id)
            if pref and pref.active_organization_id == organization_id:
                prefs.clear_active_organization(user_id, updated_by=user_id)
        raise http_error(
            403,
            f"Organization status={org.status}",
            code="org_not_active",
        )

    role_rows = auth.list_member_roles(membership.id, active_only=True)
    role_codes: list[str] = []
    permissions: set[str] = set()
    for mr in role_rows:
        row = conn.execute(
            "SELECT code FROM app_business_role WHERE id = ?", [mr.role_id]
        ).fetchone()
        if row:
            role_codes.append(str(row[0]))
        for code in auth.list_role_permissions(mr.role_id):
            permissions.add(code)

    return OrganizationContext(
        user_id=user_id,
        organization_id=organization_id,
        membership_id=membership.id,
        membership_status=membership.status,
        organization_status=org.status,
        role_codes=tuple(role_codes),
        permission_codes=frozenset(permissions),
        source=source,
        platform_role=platform_role,
        request_id=request_id,
    )


def resolve_path_organization_context(
    organization_id: int,
    request: Request,
    actor: ActorContext = Depends(get_actor),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
) -> OrganizationContext:
    """Path is authoritative; reject contradictory header/body org ids."""
    header_org = _parse_optional_org_header(x_organization_id)
    if header_org is not None and header_org != organization_id:
        raise http_error(
            400,
            "Path and X-Organization-Id disagree",
            code="context_conflict",
        )
    # Body organization_id contradiction checked in route handlers when present.
    try:
        return _load_context_for_org(
            conn,
            user_id=actor.user_id,
            organization_id=organization_id,
            source="path",
            platform_role=actor.platform_role,
            request_id=actor.request_id,
            require_active_org=False,  # permission layer decides mutations
        )
    except Exception as exc:
        if hasattr(exc, "status_code"):
            raise
        raise_domain_http(exc)


def require_organization_permission(permission_code: str):
    """FastAPI dependency factory: path org context + permission."""

    def _dep(
        ctx: OrganizationContext = Depends(resolve_path_organization_context),
    ) -> OrganizationContext:
        if not ctx.has_permission(permission_code):
            raise http_error(403, f"Missing permission {permission_code}", code="permission_denied")
        if permission_code.endswith(".view"):
            return ctx
        # Mutations require active org
        if ctx.organization_status != OrganizationStatus.ACTIVE.value:
            raise http_error(403, "Organization not operational", code="org_not_active")
        return ctx

    return _dep


def require_active_member_context(
    ctx: OrganizationContext = Depends(resolve_path_organization_context),
) -> OrganizationContext:
    if ctx.membership_status != MembershipStatus.ACTIVE.value:
        raise http_error(403, "Membership not active", code="access_revoked")
    if ctx.organization_status != OrganizationStatus.ACTIVE.value:
        raise http_error(403, "Organization not operational", code="org_not_active")
    return ctx


def _parse_optional_org_header(raw: Optional[str]) -> Optional[int]:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(str(raw).strip())
    except ValueError as exc:
        raise http_error(400, "Invalid X-Organization-Id", code="bad_header") from exc


def resolve_current_organization(
    actor: ActorContext = Depends(get_actor),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
) -> tuple[str, Optional[OrganizationContext]]:
    """Return (context_state, ctx|None) for /organizations/current.

    When the user has exactly one visible active membership and no preference,
    auto-select that organization (development / single-tenant UX).
    """
    prefs = PreferenceRepository(conn)
    header_org = _parse_optional_org_header(x_organization_id)
    pref = prefs.get_for_user(actor.user_id)
    preferred = pref.active_organization_id if pref else None

    if header_org is not None and preferred is not None and header_org != preferred:
        # Header present without path: header wins unless we treat conflict —
        # model: header > preference. No conflict if no path.
        pass

    org_id = header_org if header_org is not None else preferred
    source = "header" if header_org is not None else "preference"

    members = MembershipRepository(conn)
    orgs = OrganizationRepository(conn)

    if org_id is None:
        # Auto-select when the user has a single visible org membership.
        visible = orgs.list_for_user(actor.user_id)
        if len(visible) == 1:
            only = visible[0]
            if only.status == OrganizationStatus.ACTIVE.value:
                prefs.set_active_organization(
                    actor.user_id,
                    only.id,
                    updated_by=actor.user_id,
                )
                org_id = only.id
                source = "auto_single"
        if org_id is None:
            return "none", None

    membership = members.get_by_org_and_user(org_id, actor.user_id)
    try:
        org = orgs.get_by_id(org_id)
    except Exception:
        prefs.clear_active_organization(actor.user_id, updated_by=actor.user_id)
        return "invalid", None

    if membership is None:
        prefs.clear_active_organization(actor.user_id, updated_by=actor.user_id)
        return "invalid", None

    if membership.status != MembershipStatus.ACTIVE.value:
        prefs.clear_active_organization(actor.user_id, updated_by=actor.user_id)
        return "access_revoked", None

    if org.status != OrganizationStatus.ACTIVE.value:
        prefs.clear_active_organization(actor.user_id, updated_by=actor.user_id)
        return "invalid", None

    ctx = _load_context_for_org(
        conn,
        user_id=actor.user_id,
        organization_id=org_id,
        source=source,
        platform_role=actor.platform_role,
        request_id=actor.request_id,
        require_active_org=True,
    )
    return "active", ctx
