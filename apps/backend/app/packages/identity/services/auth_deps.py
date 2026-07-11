"""FastAPI dependencies for simple session auth."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import Depends, Header, HTTPException

from app.core.database import get_conn

from .user_service import get_user_id_from_token


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
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
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
