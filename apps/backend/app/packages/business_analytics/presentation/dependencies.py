"""Business analytics dependencies — Spec 023 / 049."""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from .error_mapping import http_error


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def _has_org_permission(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    organization_id: int,
    permission_code: str,
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM app_organization_member m
        JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        JOIN app_business_role br ON br.id = mr.role_id
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = ?
        WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
        LIMIT 1
        """,
        [permission_code, organization_id, user_id],
    ).fetchone()
    return bool(row)


def is_platform_admin_user(conn: duckdb.DuckDBPyConnection, user_id: int) -> bool:
    try:
        from app.packages.artists.identity_access.use_cases import is_platform_admin

        return bool(is_platform_admin(conn, user_id))
    except Exception:
        return False


def require_org_biz_analytics_permission(permission_code: str):
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

        if not _has_org_permission(
            conn, user_id=user_id, organization_id=org_id, permission_code=permission_code,
        ):
            raise http_error(403, f"Missing biz_analytics permission: {permission_code}", code="permission_denied")
        return {
            "user_id": user_id,
            "organization_id": org_id,
            "request_id": request_id,
            "conn": conn,
            "is_platform_admin": is_platform_admin_user(conn, user_id),
            "can_create_decision": _has_org_permission(
                conn, user_id=user_id, organization_id=org_id, permission_code="decision.create",
            ),
            "can_draft_report": _has_org_permission(
                conn, user_id=user_id, organization_id=org_id, permission_code="report.generate",
            )
            or _has_org_permission(
                conn, user_id=user_id, organization_id=org_id, permission_code="report.view",
            ),
            "can_refresh_strategic": _has_org_permission(
                conn,
                user_id=user_id,
                organization_id=org_id,
                permission_code="biz_analytics.manage",
            ),
        }
    return _dep
