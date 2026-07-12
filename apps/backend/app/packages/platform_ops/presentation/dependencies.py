"""Platform ops FastAPI dependencies — Spec 027."""

from __future__ import annotations

import uuid
from typing import Optional

import duckdb
from fastapi import Depends, Header

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.platform_rbac.infrastructure import repository as rbac_repo

from .error_mapping import http_error


def request_id_header(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> str:
    return (x_request_id or "").strip() or str(uuid.uuid4())


def require_ops_permission(permission_code: str):
    """Platform-scoped ops permission via platform_rbac."""

    def _dep(
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
        request_id: str = Depends(request_id_header),
    ) -> dict:
        if not rbac_repo.has_permission(conn, user_id, permission_code):
            raise http_error(
                403, f"Missing ops permission: {permission_code}", code="permission_denied",
            )
        return {"user_id": user_id, "request_id": request_id, "conn": conn}

    return _dep
