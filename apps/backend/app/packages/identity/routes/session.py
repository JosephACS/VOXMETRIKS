"""Session bootstrap and explicit context activation (Spec 050)."""

from __future__ import annotations

from typing import Literal, Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.database import get_write_conn
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.identity.services.session_bootstrap import (
    SessionContextError,
    activate_session_context,
    build_session_bootstrap,
    complete_first_access,
)

router = APIRouter(prefix="/session", tags=["Session"])

_STRICT = ConfigDict(strict=True, extra="forbid")


class SessionContextBody(BaseModel):
    model_config = _STRICT
    space_key: str = Field(min_length=1, max_length=128)


class FirstAccessBody(BaseModel):
    model_config = _STRICT
    intent: Optional[str] = None


class SessionCapabilityModel(BaseModel):
    model_config = _STRICT
    code: str
    allowed: bool
    reason: Optional[str] = None


class SessionSpaceModel(BaseModel):
    model_config = _STRICT
    key: str
    kind: Literal["personal", "organization", "artist", "data_ops", "platform_admin"]
    display_name: str
    capabilities: list[SessionCapabilityModel]
    home_path: str


class SessionUserModel(BaseModel):
    model_config = _STRICT
    id: int
    display_name: str
    identity_role: str


class SessionSecurityModel(BaseModel):
    model_config = _STRICT
    email_verified: bool
    profile_pin_enabled: bool


class SessionPendingActionModel(BaseModel):
    model_config = _STRICT
    code: str


class SessionBootstrapResponse(BaseModel):
    model_config = _STRICT
    user: SessionUserModel
    security: SessionSecurityModel
    spaces: list[SessionSpaceModel]
    active_space_key: str
    pending_actions: list[SessionPendingActionModel]
    recommended_path: str


def _raise(exc: SessionContextError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def _validated(payload: dict) -> SessionBootstrapResponse:
    return SessionBootstrapResponse.model_validate(payload)


@router.get("/bootstrap", response_model=SessionBootstrapResponse)
def get_session_bootstrap(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> SessionBootstrapResponse:
    try:
        return _validated(build_session_bootstrap(conn, user_id))
    except SessionContextError as exc:
        _raise(exc)
        raise


@router.post("/context", response_model=SessionBootstrapResponse)
def post_session_context(
    body: SessionContextBody,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> SessionBootstrapResponse:
    try:
        return _validated(activate_session_context(conn, user_id, body.space_key))
    except SessionContextError as exc:
        _raise(exc)
        raise


@router.post("/first-access", response_model=SessionBootstrapResponse)
def post_first_access(
    body: FirstAccessBody,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> SessionBootstrapResponse:
    """Record that guided first-run actions were seen. Never grants a role."""
    _ = body.intent
    complete_first_access(conn, user_id)
    return _validated(build_session_bootstrap(conn, user_id))
