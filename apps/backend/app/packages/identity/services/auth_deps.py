"""FastAPI dependencies for simple session auth and reusable capability gates.

Spec 037 — deny-by-default for enterprise/technical surfaces; personal music
capabilities remain ``require_user_id`` only.
"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import Depends, Header, HTTPException

from app.core.database import get_conn

from .user_service import get_user_id_from_token

# Identity roles (app_user.role). Do not invent new login roles.
STAFF_IDENTITY_ROLES = frozenset({"admin", "engineer"})
ADMIN_IDENTITY_ROLES = frozenset({"admin"})
TECHNICAL_IDENTITY_ROLES = frozenset({"admin", "engineer"})


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


extract_token = _extract_token


def get_optional_user_id(
    authorization: Optional[str] = Header(None),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> Optional[int]:
    token = _extract_token(authorization)
    if not token:
        return None
    return get_user_id_from_token(conn, token)


def require_user_id(
    user_id: Optional[int] = Depends(get_optional_user_id),
) -> int:
    """Authenticated personal session (music, profile, own activity)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def get_identity_role(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> str:
    """Return normalized ``app_user.role`` for the authenticated user."""
    from .user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return (user.get("role") or "user").lower()


def require_roles(*allowed: str, detail: str = "Insufficient permissions"):
    """Factory: require identity role ∈ allowed (deny-by-default)."""

    allowed_set = frozenset(a.lower() for a in allowed)

    def _dep(
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    ) -> int:
        from .user_service import _fetch_user

        user = _fetch_user(conn, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        role = (user.get("role") or "user").lower()
        if role not in allowed_set:
            raise HTTPException(status_code=403, detail=detail)
        return user_id

    return _dep


def require_staff_identity(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> int:
    """Enterprise staff surfaces (Workpanel, operational reports): admin | engineer.

    Listeners must receive 403 with no payload (spec 037 P0).
    """
    from .user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = (user.get("role") or "user").lower()
    if role not in STAFF_IDENTITY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Staff role required",
        )
    return user_id


def require_enterprise_access(
    user_id: int = Depends(require_staff_identity),
) -> int:
    """Alias: enterprise operational capability (identity staff gate)."""
    return user_id


def require_technical_access(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> int:
    """Data engineering / warehouse tools: admin | engineer."""
    from .user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = (user.get("role") or "user").lower()
    if role not in TECHNICAL_IDENTITY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Technical role required",
        )
    return user_id


def require_engineer_user(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> int:
    """Engineering access: admin OR data engineer (ELT pipeline + analytics)."""
    from .user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = (user.get("role") or "user").lower()
    if role not in {"admin", "engineer"}:
        raise HTTPException(
            status_code=403,
            detail="Engineer role required",
        )
    return user_id


def require_admin_user(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> int:
    """Catalog mutations (artists/tracks/genres) are admin-only.

    Data engineers manage the ELT pipeline and analytics, but must never edit
    the music catalog by hand. Mirrors FE isCatalogSteward (admin only).
    """
    from .user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = (user.get("role") or "user").lower()
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede modificar el catálogo musical.",
        )
    return user_id


def resolve_optional_org_membership(
    *,
    user_id: int,
    organization_id: Optional[int],
    conn: duckdb.DuckDBPyConnection,
) -> Optional[int]:
    """Validate optional org header for staff surfaces.

    - No header → None (platform/staff scope without org filter).
    - Invalid id → 400.
    - Not a member / inactive → 403 (no data leak).
    """
    if organization_id is None:
        return None
    if organization_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid X-Organization-Id")
    try:
        row = conn.execute(
            """
            SELECT m.status
            FROM app_organization_member m
            WHERE m.organization_id = ? AND m.user_id = ?
            LIMIT 1
            """,
            [organization_id, user_id],
        ).fetchone()
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="Organization access denied",
        ) from None
    if row is None:
        raise HTTPException(status_code=403, detail="Organization access denied")
    status = str(row[0] or "").lower()
    if status not in {"active", "activo"}:
        raise HTTPException(status_code=403, detail="Organization access denied")
    return organization_id


def ensure_self_or_admin(
    *,
    target_user_id: int,
    current_user_id: int,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Raise 403 unless ``current_user_id`` owns ``target_user_id`` or is admin.

    Spec 014 D1 — prevent arbitrary user_id probing of private insights.
    """
    if target_user_id == current_user_id:
        return
    from .user_service import _fetch_user

    user = _fetch_user(conn, current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = (user.get("role") or "user").lower()
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's data",
        )
