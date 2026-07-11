"""Organizations HTTP router — Spec 016 I3 · /api/v1."""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_write_conn
from app.packages.organizations.application.context import OrganizationContext
from app.packages.organizations.application.dto import (
    ActorContext,
    CreateOrganizationCommand,
)
from app.packages.organizations.application.use_cases.create_organization import (
    CreateOrganization,
)
from app.packages.organizations.application.use_cases.invitations import (
    InvitationUseCases,
)
from app.packages.organizations.application.use_cases.membership import (
    MembershipUseCases,
)
from app.packages.organizations.application.use_cases.organization_ops import (
    ChangeOrganizationStatus,
    UpdateOrganizationProfile,
)
from app.packages.organizations.application.use_cases.preference import (
    PreferenceUseCases,
)
from app.packages.organizations.application.use_cases.roles import RoleUseCases
from app.packages.organizations.domain.entities import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.packages.organizations.domain.rules import normalize_slug
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.invitation_repository import (
    InvitationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)
from app.packages.organizations.presentation.dependencies import (
    get_actor,
    require_active_member_context,
    require_organization_permission,
    resolve_current_organization,
    resolve_path_organization_context,
)
from app.packages.organizations.presentation.error_mapping import raise_domain_http
from app.packages.organizations.presentation.schemas import (
    AcceptInvitationResponse,
    AuditEntryOut,
    CloseOrganizationRequest,
    CurrentOrganizationResponse,
    InvitationCreateRequest,
    InvitationCreateResponse,
    InvitationOut,
    MemberActionRequest,
    MemberRolesPutRequest,
    MembershipOut,
    OrganizationCreateRequest,
    OrganizationCreateResponse,
    OrganizationOut,
    OrganizationUpdateRequest,
    PaginatedAudit,
    PaginatedInvitations,
    PaginatedMembers,
    PermissionOut,
    RoleOut,
)

router = APIRouter(tags=["Organizations"])


def _org_out(o: Organization) -> OrganizationOut:
    return OrganizationOut(
        id=o.id,
        display_name=o.display_name,
        legal_name=o.legal_name,
        slug=o.slug,
        organization_type=o.organization_type,
        country_code=o.country_code,
        timezone=o.timezone,
        default_currency=o.default_currency,
        status=o.status,
        created_by=o.created_by,
        created_at=o.created_at,
        updated_at=o.updated_at,
        closed_at=o.closed_at,
        is_demo=o.is_demo,
    )


def _member_out(m: OrganizationMember) -> MembershipOut:
    return MembershipOut(
        id=m.id,
        organization_id=m.organization_id,
        user_id=m.user_id,
        status=m.status,
        joined_at=m.joined_at,
        suspended_at=m.suspended_at,
        left_at=m.left_at,
        removed_at=m.removed_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _invite_out(i: OrganizationInvitation) -> InvitationOut:
    return InvitationOut(
        id=i.id,
        organization_id=i.organization_id,
        email_normalized=i.email_normalized,
        status=i.status,
        expires_at=i.expires_at,
        invited_by=i.invited_by,
        initial_role_code=i.initial_role_code,
        accepted_by=i.accepted_by,
        accepted_at=i.accepted_at,
        revoked_by=i.revoked_by,
        revoked_at=i.revoked_at,
        created_at=i.created_at,
        updated_at=i.updated_at,
    )


def _page_bounds(page: int, limit: int) -> tuple[int, int, int]:
    page = max(1, page)
    lim = min(max(1, limit), 100)
    offset = (page - 1) * lim
    return page, lim, offset


# ── Organizations ───────────────────────────────────────────────────────────


@router.post("/organizations", status_code=201, response_model=OrganizationCreateResponse)
def create_organization(
    body: OrganizationCreateRequest,
    actor: ActorContext = Depends(get_actor),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        slug = body.slug.strip() if body.slug else normalize_slug(body.display_name)
        result = CreateOrganization(conn).execute(
            CreateOrganizationCommand(
                actor=actor,
                display_name=body.display_name,
                slug=slug,
                organization_type=body.organization_type,
                country_code=body.country_code,
                timezone=body.timezone,
                default_currency=body.default_currency,
                legal_name=body.legal_name,
                make_active=body.activate,
            )
        )
        auth = AuthorizationRepository(conn)
        roles = [
            r
            for r in (
                conn.execute(
                    """
                    SELECT br.code FROM app_member_role mr
                    JOIN app_business_role br ON br.id = mr.role_id
                    WHERE mr.member_id = ? AND mr.status = 'active'
                    """,
                    [result.membership.id],
                ).fetchall()
            )
            for r in [str(r[0])]
        ]
        _ = auth
        return OrganizationCreateResponse(
            organization=_org_out(result.organization),
            membership=_member_out(result.membership),
            roles=roles,
            reused_existing=result.reused_existing,
            idempotency_mode=result.idempotency_mode,
        )
    except Exception as exc:
        raise_domain_http(exc)


@router.get("/organizations", response_model=list[OrganizationOut])
def list_my_organizations(
    actor: ActorContext = Depends(get_actor),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        orgs = OrganizationRepository(conn).list_for_user(actor.user_id)
        return [_org_out(o) for o in orgs]
    except Exception as exc:
        raise_domain_http(exc)


@router.get("/organizations/current", response_model=CurrentOrganizationResponse)
def get_current_organization(
    resolved=Depends(resolve_current_organization),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    state, ctx = resolved
    if state != "active" or ctx is None:
        return CurrentOrganizationResponse(context=state)  # type: ignore[arg-type]
    org = OrganizationRepository(conn).get_by_id(ctx.organization_id)
    member = MembershipRepository(conn).get_by_id(ctx.membership_id)
    return CurrentOrganizationResponse(
        context="active",
        organization=_org_out(org),
        membership=_member_out(member),
        roles=list(ctx.role_codes),
        permissions=sorted(ctx.permission_codes),
        source=ctx.source,
    )


@router.get("/organizations/{organization_id}", response_model=OrganizationOut)
def get_organization(
    organization_id: int,
    ctx: OrganizationContext = Depends(
        require_organization_permission("organization.view")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        return _org_out(OrganizationRepository(conn).get_by_id(organization_id))
    except Exception as exc:
        raise_domain_http(exc)


@router.patch("/organizations/{organization_id}", response_model=OrganizationOut)
def update_organization(
    organization_id: int,
    body: OrganizationUpdateRequest,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("organization.update")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        result = UpdateOrganizationProfile(conn).execute(
            actor,
            organization_id,
            display_name=body.display_name,
            legal_name=body.legal_name,
            organization_type=body.organization_type,
            country_code=body.country_code,
            timezone=body.timezone,
            default_currency=body.default_currency,
        )
        return _org_out(result.data)
    except Exception as exc:
        raise_domain_http(exc)


@router.post("/organizations/{organization_id}/close", response_model=OrganizationOut)
def close_organization(
    organization_id: int,
    body: CloseOrganizationRequest | None = None,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("organization.close")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        result = ChangeOrganizationStatus(conn).execute(
            actor,
            organization_id,
            "closed",
            reason=(body.reason if body else None),
        )
        return _org_out(result.data)
    except Exception as exc:
        raise_domain_http(exc)


@router.post("/organizations/{organization_id}/activate", response_model=CurrentOrganizationResponse)
def activate_organization(
    organization_id: int,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(require_active_member_context),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        result = PreferenceUseCases(conn).set_active(actor, organization_id)
        org = OrganizationRepository(conn).get_by_id(organization_id)
        member = MembershipRepository(conn).get_by_org_and_user(
            organization_id, actor.user_id
        )
        auth = AuthorizationRepository(conn)
        roles = auth.list_member_roles(member.id)
        role_codes = []
        perms: set[str] = set()
        for mr in roles:
            row = conn.execute(
                "SELECT code FROM app_business_role WHERE id = ?", [mr.role_id]
            ).fetchone()
            if row:
                role_codes.append(str(row[0]))
            perms.update(auth.list_role_permissions(mr.role_id))
        _ = result
        return CurrentOrganizationResponse(
            context="active",
            organization=_org_out(org),
            membership=_member_out(member),
            roles=role_codes,
            permissions=sorted(perms),
            source="path",
        )
    except Exception as exc:
        raise_domain_http(exc)


# ── Members ─────────────────────────────────────────────────────────────────


@router.get(
    "/organizations/{organization_id}/members",
    response_model=PaginatedMembers,
)
def list_members(
    organization_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: OrganizationContext = Depends(require_organization_permission("member.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        page, lim, offset = _page_bounds(page, limit)
        uc = MembershipUseCases(conn)
        items = uc.list_by_organization(
            ActorContext(user_id=ctx.user_id, request_id=ctx.request_id),
            organization_id,
            limit=lim,
            offset=offset,
        )
        total = uc.count_by_organization(organization_id)
        return PaginatedMembers(
            items=[_member_out(m) for m in items],
            page=page,
            limit=lim,
            total=total,
        )
    except Exception as exc:
        raise_domain_http(exc)


@router.patch(
    "/organizations/{organization_id}/members/{member_id}",
    response_model=MembershipOut,
)
def patch_member(
    organization_id: int,
    member_id: int,
    body: MemberActionRequest,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(resolve_path_organization_context),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    uc = MembershipUseCases(conn)
    try:
        # Ensure target belongs to this org (anti-IDOR)
        target = uc.get_membership(member_id)
        if target.organization_id != organization_id:
            from app.packages.organizations.presentation.error_mapping import http_error

            raise http_error(404, "Not found", code="not_found")

        if body.action == "leave":
            if target.user_id != actor.user_id:
                from app.packages.organizations.presentation.error_mapping import http_error

                raise http_error(403, "Can only leave as self", code="permission_denied")
            result = uc.leave_organization(actor, organization_id)
        elif body.action == "suspend":
            if not ctx.has_permission("member.suspend"):
                from app.packages.organizations.presentation.error_mapping import http_error

                raise http_error(403, "Missing permission member.suspend", code="permission_denied")
            if ctx.organization_status != "active":
                from app.packages.organizations.presentation.error_mapping import http_error

                raise http_error(403, "Organization not operational", code="org_not_active")
            result = uc.suspend_member(actor, organization_id, member_id)
        elif body.action == "reactivate":
            if not ctx.has_permission("member.suspend"):
                from app.packages.organizations.presentation.error_mapping import http_error

                raise http_error(403, "Missing permission", code="permission_denied")
            if ctx.organization_status != "active":
                from app.packages.organizations.presentation.error_mapping import http_error

                raise http_error(403, "Organization not operational", code="org_not_active")
            result = uc.reactivate_member(actor, organization_id, member_id)
        else:
            from app.packages.organizations.presentation.error_mapping import http_error

            raise http_error(422, "Invalid action", code="validation_error")
        return _member_out(result.data)
    except Exception as exc:
        raise_domain_http(exc)


@router.post(
    "/organizations/{organization_id}/members/{member_id}/remove",
    response_model=MembershipOut,
)
def remove_member(
    organization_id: int,
    member_id: int,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("member.remove")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        uc = MembershipUseCases(conn)
        target = uc.get_membership(member_id)
        if target.organization_id != organization_id:
            from app.packages.organizations.presentation.error_mapping import http_error

            raise http_error(404, "Not found", code="not_found")
        result = uc.remove_member(actor, organization_id, member_id)
        return _member_out(result.data)
    except Exception as exc:
        raise_domain_http(exc)


# ── Invitations ─────────────────────────────────────────────────────────────


@router.post(
    "/organizations/{organization_id}/invitations",
    status_code=201,
    response_model=InvitationCreateResponse,
)
def create_invitation(
    organization_id: int,
    body: InvitationCreateRequest,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("member.invite")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        role = body.role_codes[0]
        result = InvitationUseCases(conn).create(
            actor,
            organization_id,
            body.email,
            role,
            ttl_days=body.ttl_days,
        )
        return InvitationCreateResponse(
            invitation_id=result.invitation.id,
            expires_at=result.invitation.expires_at,
            invite_token=result.invite_token,
            returned_once=result.returned_once,
            delivery_status=result.email_delivery_status,
            invitation=_invite_out(result.invitation),
        )
    except Exception as exc:
        raise_domain_http(exc)


@router.get(
    "/organizations/{organization_id}/invitations",
    response_model=PaginatedInvitations,
)
def list_invitations(
    organization_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: OrganizationContext = Depends(resolve_path_organization_context),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not (
        ctx.has_permission("member.invite")
        or ctx.has_permission("invitation.view")
    ):
        from app.packages.organizations.presentation.error_mapping import http_error

        raise http_error(403, "Missing invitation view permission", code="permission_denied")
    try:
        page, lim, offset = _page_bounds(page, limit)
        items = InvitationRepository(conn).list_by_organization(
            organization_id, limit=lim, offset=offset
        )
        total = InvitationRepository(conn).count_by_organization(organization_id)
        return PaginatedInvitations(
            items=[_invite_out(i) for i in items],
            page=page,
            limit=lim,
            total=total,
        )
    except Exception as exc:
        raise_domain_http(exc)


@router.post(
    "/invitations/{token}/accept",
    response_model=AcceptInvitationResponse,
)
def accept_invitation(
    token: str,
    actor: ActorContext = Depends(get_actor),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        result = InvitationUseCases(conn).accept(actor, token)
        return AcceptInvitationResponse(
            organization=_org_out(result.organization),
            membership=_member_out(result.membership),
        )
    except Exception as exc:
        raise_domain_http(exc)


@router.post(
    "/organizations/{organization_id}/invitations/{invitation_id}/revoke",
    response_model=InvitationOut,
)
def revoke_invitation(
    organization_id: int,
    invitation_id: int,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("invitation.revoke")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        InvitationRepository(conn).get_by_id_in_organization(
            invitation_id, organization_id
        )
        result = InvitationUseCases(conn).revoke(actor, organization_id, invitation_id)
        return _invite_out(result.data)
    except Exception as exc:
        raise_domain_http(exc)


@router.post(
    "/organizations/{organization_id}/invitations/{invitation_id}/resend",
    response_model=InvitationCreateResponse,
)
def resend_invitation(
    organization_id: int,
    invitation_id: int,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("member.invite")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        InvitationRepository(conn).get_by_id_in_organization(
            invitation_id, organization_id
        )
        result = InvitationUseCases(conn).resend(actor, organization_id, invitation_id)
        return InvitationCreateResponse(
            invitation_id=result.invitation.id,
            expires_at=result.invitation.expires_at,
            invite_token=result.invite_token,
            returned_once=True,
            delivery_status=result.email_delivery_status,
            invitation=_invite_out(result.invitation),
        )
    except Exception as exc:
        raise_domain_http(exc)


# ── Roles / permissions ─────────────────────────────────────────────────────


@router.get("/organizations/{organization_id}/roles", response_model=list[RoleOut])
def list_roles(
    organization_id: int,
    ctx: OrganizationContext = Depends(require_organization_permission("role.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = organization_id, ctx
    rows = conn.execute(
        """
        SELECT id, code, display_name, description, scope, is_system, is_active
        FROM app_business_role
        WHERE scope = 'organization'
        ORDER BY code
        """
    ).fetchall()
    return [
        RoleOut(
            id=int(r[0]),
            code=str(r[1]),
            display_name=str(r[2]),
            description=str(r[3]),
            scope=str(r[4]),
            is_system=bool(r[5]),
            is_active=bool(r[6]),
        )
        for r in rows
    ]


@router.get(
    "/organizations/{organization_id}/permissions",
    response_model=list[PermissionOut],
)
def list_permissions(
    organization_id: int,
    ctx: OrganizationContext = Depends(require_organization_permission("role.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = organization_id, ctx
    rows = conn.execute(
        """
        SELECT id, code, description, domain, is_active
        FROM app_permission
        WHERE is_active = TRUE
        ORDER BY code
        """
    ).fetchall()
    return [
        PermissionOut(
            id=int(r[0]),
            code=str(r[1]),
            description=str(r[2]),
            domain=str(r[3]),
            is_active=bool(r[4]),
        )
        for r in rows
    ]


@router.put(
    "/organizations/{organization_id}/members/{member_id}/roles",
    response_model=list[str],
)
def put_member_roles(
    organization_id: int,
    member_id: int,
    body: MemberRolesPutRequest,
    actor: ActorContext = Depends(get_actor),
    ctx: OrganizationContext = Depends(
        require_organization_permission("role.assign")
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        member = MembershipRepository(conn).get_by_id(member_id)
        if member.organization_id != organization_id:
            from app.packages.organizations.presentation.error_mapping import http_error

            raise http_error(404, "Not found", code="not_found")
        roles = RoleUseCases(conn)
        for code in body.assign:
            roles.assign_member_role(actor, organization_id, member_id, code)
        for code in body.revoke:
            roles.revoke_member_role(actor, organization_id, member_id, code)
        active = roles.list_member_roles(actor, organization_id, member_id)
        codes = []
        for mr in active:
            row = conn.execute(
                "SELECT code FROM app_business_role WHERE id = ?", [mr.role_id]
            ).fetchone()
            if row:
                codes.append(str(row[0]))
        return codes
    except Exception as exc:
        raise_domain_http(exc)


# ── Audit ───────────────────────────────────────────────────────────────────


@router.get(
    "/organizations/{organization_id}/audit-log",
    response_model=PaginatedAudit,
)
def list_audit_log(
    organization_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: OrganizationContext = Depends(require_organization_permission("audit.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    _ = ctx
    try:
        offset = (max(1, page) - 1) * min(max(1, limit), 100)
        lim = min(max(1, limit), 100)
        total = int(
            conn.execute(
                "SELECT COUNT(*) FROM app_audit_log WHERE organization_id = ?",
                [organization_id],
            ).fetchone()[0]
        )
        entries = AuditRepository(conn).list_by_organization(
            organization_id, limit=lim, offset=offset
        )
        items = []
        for e in entries:
            prev = json.loads(e.previous_values_json) if e.previous_values_json else None
            new = json.loads(e.new_values_json) if e.new_values_json else None
            items.append(
                AuditEntryOut(
                    id=e.id,
                    organization_id=e.organization_id,
                    actor_user_id=e.actor_user_id,
                    action=e.action,
                    target_type=e.target_type,
                    target_id=e.target_id,
                    reason=e.reason,
                    request_id=e.request_id,
                    source=e.source,
                    result=e.result,
                    occurred_at=e.occurred_at,
                    previous_values=prev,
                    new_values=new,
                )
            )
        return PaginatedAudit(items=items, page=max(1, page), limit=lim, total=total)
    except Exception as exc:
        raise_domain_http(exc)
