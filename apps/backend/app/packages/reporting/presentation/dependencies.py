"""Reporting FastAPI dependencies — Spec 024."""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import (
    require_user_id,
    resolve_optional_org_membership,
)
from app.packages.identity.services.user_service import _fetch_user

from .error_mapping import http_error


def get_current_report_role(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> str:
    """Resolve the platform identity role used by the shared report gate."""

    user = _fetch_user(conn, user_id)
    return str((user or {}).get("role") or "user").lower()


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def require_org_reporting_permission(permission_code: str):
    """Require org membership + reporting/decision permission via X-Organization-Id."""

    def _dep(
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
        request_id: str = Depends(request_id_header),
        x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
    ) -> dict:
        if not x_organization_id or not x_organization_id.strip():
            raise http_error(400, "X-Organization-Id header is required", code="missing_org_header")
        try:
            org_id = int(x_organization_id.strip())
        except ValueError:
            raise http_error(400, "Invalid X-Organization-Id", code="bad_header")

        perm_row = conn.execute(
            """
            SELECT 1
            FROM app_organization_member m
            JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
            JOIN app_business_role br ON br.id = mr.role_id
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id AND p.code = ?
            WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
            LIMIT 1
            """,
            [permission_code, org_id, user_id],
        ).fetchone()
        if not perm_row:
            raise http_error(
                403, f"Missing reporting permission: {permission_code}", code="permission_denied",
            )

        return {
            "user_id": user_id,
            "organization_id": org_id,
            "request_id": request_id,
            "conn": conn,
        }

    return _dep


def resolve_staff_or_org_report_access(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    identity_role: str = Depends(get_current_report_role),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
) -> dict:
    """Allow platform staff or an organization member with ``report.view``.

    Personal listeners without an active organization remain forbidden. Organization
    access is always scoped to the verified organization from the request header.
    """

    return resolve_report_access_context(
        user_id=user_id,
        conn=conn,
        identity_role=identity_role,
        x_organization_id=x_organization_id,
    )


def resolve_report_access_context(
    *,
    user_id: int,
    conn: duckdb.DuckDBPyConnection,
    identity_role: str,
    x_organization_id: Optional[str],
) -> dict:
    """Build a verified report context for an already authenticated identity."""

    identity_role = str(identity_role or "user").lower()
    raw_header = (x_organization_id or "").strip()

    if identity_role in {"admin", "engineer"}:
        organization_id = None
        if raw_header:
            try:
                requested_org = int(raw_header)
            except ValueError as exc:
                raise http_error(400, "Invalid X-Organization-Id", code="bad_header") from exc
            organization_id = resolve_optional_org_membership(
                user_id=user_id,
                organization_id=requested_org,
                conn=conn,
            )
        return {
            "user_id": user_id,
            "identity_role": identity_role,
            "access_role": identity_role,
            "organization_id": organization_id,
            "organization_access": False,
            "conn": conn,
        }

    if not raw_header:
        raise http_error(
            403,
            "An active organization with report access is required",
            code="permission_denied",
        )
    try:
        organization_id = int(raw_header)
    except ValueError as exc:
        raise http_error(400, "Invalid X-Organization-Id", code="bad_header") from exc

    allowed = conn.execute(
        """
        SELECT 1
        FROM app_organization_member m
        JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        JOIN app_business_role br ON br.id = mr.role_id AND br.is_active = TRUE
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'report.view'
        JOIN app_organization o ON o.id = m.organization_id AND o.status = 'active'
        WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
        LIMIT 1
        """,
        [organization_id, user_id],
    ).fetchone()
    if not allowed:
        raise http_error(403, "Missing reporting permission: report.view", code="permission_denied")

    return {
        "user_id": user_id,
        "identity_role": identity_role,
        # Organization owners/admins receive the business report catalog, while
        # query execution remains locked to their verified organization id.
        "access_role": "admin",
        "organization_id": organization_id,
        "organization_access": True,
        "conn": conn,
    }
