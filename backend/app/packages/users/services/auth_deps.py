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
