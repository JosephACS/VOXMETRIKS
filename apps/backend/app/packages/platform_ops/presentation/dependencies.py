"""Platform ops FastAPI dependencies — Spec 027."""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.identity.services.user_service import _fetch_user
from app.packages.platform_rbac.infrastructure import repository as rbac_repo

from .error_mapping import http_error

# Spec 046 platform-admin mirror: identity admin OR CRM platform_admin
# may access core ops.view / ops.manage without explicit RBAC grants.
_PLATFORM_ADMIN_OPS_PERMISSIONS = frozenset({"ops.view", "ops.manage"})


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def _is_platform_admin(conn: duckdb.DuckDBPyConnection, user_id: int) -> bool:
    """Mirror FE platformAdminGuard / Spec 046 is_platform_admin."""
    user = _fetch_user(conn, user_id)
    if user and (user.get("role") or "").lower() == "admin":
        return True
    roles = rbac_repo.list_user_platform_roles(conn, user_id)
    return "platform_admin" in roles


def require_ops_permission(permission_code: str):
    """Platform-scoped ops permission via platform_rbac (or platform admin for view/manage)."""

    def _dep(
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
        request_id: str = Depends(request_id_header),
    ) -> dict:
        allowed = rbac_repo.has_permission(conn, user_id, permission_code)
        if (
            not allowed
            and permission_code in _PLATFORM_ADMIN_OPS_PERMISSIONS
            and _is_platform_admin(conn, user_id)
        ):
            allowed = True
        if not allowed:
            raise http_error(
                403, f"Missing ops permission: {permission_code}", code="permission_denied",
            )
        return {"user_id": user_id, "request_id": request_id, "conn": conn}

    return _dep
