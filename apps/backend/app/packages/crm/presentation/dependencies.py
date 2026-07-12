"""CRM FastAPI dependencies — Spec 017.

Platform-scoped RBAC only.
- require_crm_permission(code): checks app_user_platform_role/app_platform_permission
- Does NOT use org roles (016 roles do not grant CRM access)
- Does NOT treat identity roles admin/engineer as CRM access
"""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header, HTTPException

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.platform_rbac.infrastructure import repository as rbac_repo

from .error_mapping import http_error


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def get_crm_actor(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    request_id: str = Depends(request_id_header),
) -> dict:
    """Return minimal actor context for CRM endpoints."""
    return {
        "user_id": user_id,
        "request_id": request_id,
        "conn": conn,
    }


def require_crm_permission(permission_code: str):
    """FastAPI dependency factory: require a specific CRM platform permission.

    403 if the authenticated user does not hold an active platform role
    that grants permission_code. Identity roles (admin/engineer) are NOT
    honoured as CRM access.
    """

    def _dep(
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
        request_id: str = Depends(request_id_header),
    ) -> dict:
        if not rbac_repo.has_permission(conn, user_id, permission_code):
            raise http_error(
                403,
                f"Missing CRM permission: {permission_code}",
                code="permission_denied",
            )
        return {
            "user_id": user_id,
            "request_id": request_id,
            "conn": conn,
        }

    return _dep


def require_org_owner(
    organization_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> dict:
    """Verify the authenticated user is an active owner of organization_id.

    Used for Path A conversion confirm-link endpoint.
    This is an org-level ownership check, not a CRM permission.
    """
    row = conn.execute(
        """
        SELECT 1
        FROM app_organization_member m
        JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        JOIN app_business_role br ON br.id = mr.role_id AND br.code = 'owner'
        WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
        LIMIT 1
        """,
        [organization_id, user_id],
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=403,
            detail={"message": "Must be an active owner of the organization", "code": "not_org_owner"},
        )
    return {"user_id": user_id, "organization_id": organization_id, "conn": conn}
