"""Security API — profile PIN, devices, password change, activity."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.database import get_write_conn
from app.core.rate_limit import check_auth_rate_limit
from app.packages.identity.services.auth_deps import extract_token, require_user_id
from app.packages.identity.services.profile_security import (
    ProfilePinError,
    authorize_device,
    change_account_password,
    change_pin,
    disable_pin,
    enable_pin,
    ensure_profile_security_tables,
    get_pin_status,
    list_devices,
    list_security_events,
    reset_pin_with_password,
    revoke_device,
    revoke_other_devices,
    revoke_other_sessions,
    unlock_with_pin_on_device,
    update_pin_preferences,
    verify_pin,
)
from app.packages.personal_subscriptions.domain.errors import PersonalForbiddenError

router = APIRouter(prefix="/security", tags=["Security"])


def _raise(exc: Exception) -> None:
    if isinstance(exc, ProfilePinError):
        status = 400
        if exc.code == "pin_locked":
            status = 429
        elif exc.code == "pin_incorrect":
            status = 401
        elif exc.code in ("bad_password", "device_required"):
            status = 403
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": str(exc)})
    if isinstance(exc, PersonalForbiddenError):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": str(exc)})
    raise HTTPException(status_code=400, detail={"code": "security_error", "message": str(exc)})


class PinEnableBody(BaseModel):
    password: str
    pin: str = Field(min_length=4, max_length=6)
    pin_confirm: str = Field(min_length=4, max_length=6)
    require_on_select: bool = True
    lock_on_switch: bool = True


class PinVerifyBody(BaseModel):
    pin: str = Field(min_length=4, max_length=6)
    device_token: Optional[str] = None


class PinPrefsBody(BaseModel):
    require_on_select: Optional[bool] = None
    lock_on_switch: Optional[bool] = None


class PasswordOnlyBody(BaseModel):
    password: str


class PasswordChangeBody(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    revoke_other_sessions: bool = True


class DeviceAuthorizeBody(BaseModel):
    password: str
    device_label: Optional[str] = None
    browser: Optional[str] = None
    os_name: Optional[str] = None


class DeviceRevokeOthersBody(BaseModel):
    keep_device_token: Optional[str] = None


class PinUnlockSwitchBody(BaseModel):
    target_user_id: int
    pin: str = Field(min_length=4, max_length=6)
    device_token: str


@router.get("/pin")
def pin_status(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ensure_profile_security_tables(conn)
    return get_pin_status(conn, user_id)


@router.post("/pin/enable")
def pin_enable(
    body: PinEnableBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return enable_pin(
            conn,
            user_id,
            password=body.password,
            pin=body.pin,
            pin_confirm=body.pin_confirm,
            require_on_select=body.require_on_select,
            lock_on_switch=body.lock_on_switch,
        )
    except Exception as e:
        _raise(e)


@router.post("/pin/change")
def pin_change(
    body: PinEnableBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return change_pin(
            conn,
            user_id,
            password=body.password,
            pin=body.pin,
            pin_confirm=body.pin_confirm,
        )
    except Exception as e:
        _raise(e)


@router.post("/pin/disable")
def pin_disable(
    body: PasswordOnlyBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return disable_pin(conn, user_id, password=body.password)
    except Exception as e:
        _raise(e)


@router.post("/pin/reset")
def pin_reset(
    body: PinEnableBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return reset_pin_with_password(
            conn,
            user_id,
            password=body.password,
            pin=body.pin,
            pin_confirm=body.pin_confirm,
        )
    except Exception as e:
        _raise(e)


@router.post("/pin/verify")
def pin_verify(
    body: PinVerifyBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(
        request, max(5, cfg.effective_auth_rate_limit // 2), cfg.auth_rate_window_sec
    )
    try:
        return verify_pin(conn, user_id, body.pin, device_token=body.device_token)
    except Exception as e:
        _raise(e)


@router.patch("/pin/preferences")
def pin_prefs(
    body: PinPrefsBody,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return update_pin_preferences(
            conn,
            user_id,
            require_on_select=body.require_on_select,
            lock_on_switch=body.lock_on_switch,
        )
    except Exception as e:
        _raise(e)


@router.post("/pin/unlock-switch")
def pin_unlock_switch(
    body: PinUnlockSwitchBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    """Switch to another household member using THEIR device token + PIN."""
    cfg = get_settings()
    check_auth_rate_limit(
        request, max(5, cfg.effective_auth_rate_limit // 2), cfg.auth_rate_window_sec
    )
    from app.packages.personal_subscriptions.application.use_cases import get_household

    hh = get_household(conn, user_id)
    if not hh or not any(int(m["user_id"]) == int(body.target_user_id) for m in hh["members"]):
        raise HTTPException(
            status_code=403,
            detail={"code": "forbidden", "message": "Ese perfil no pertenece a tu grupo"},
        )
    if int(body.target_user_id) == int(user_id):
        try:
            return verify_pin(conn, user_id, body.pin, device_token=body.device_token)
        except Exception as e:
            _raise(e)
    try:
        return unlock_with_pin_on_device(
            conn,
            target_user_id=int(body.target_user_id),
            pin=body.pin,
            device_token=body.device_token,
        )
    except Exception as e:
        _raise(e)


@router.get("/devices")
def devices_list(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    return {"items": list_devices(conn, user_id)}


@router.post("/devices/authorize")
def devices_authorize(
    body: DeviceAuthorizeBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return authorize_device(
            conn,
            user_id,
            password=body.password,
            device_label=body.device_label,
            browser=body.browser,
            os_name=body.os_name,
        )
    except Exception as e:
        _raise(e)


@router.post("/devices/{device_id}/revoke")
def devices_revoke(
    device_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return revoke_device(conn, user_id, device_id)
    except Exception as e:
        _raise(e)


@router.post("/devices/revoke-others")
def devices_revoke_others(
    body: DeviceRevokeOthersBody | None = None,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    keep = body.keep_device_token if body else None
    return revoke_other_devices(conn, user_id, keep_device_token=keep)


@router.post("/sessions/revoke-others")
def sessions_revoke_others(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    authorization: Optional[str] = Header(None),
):
    token = extract_token(authorization)
    return revoke_other_sessions(conn, user_id, keep_token=token)


@router.post("/password/change")
def password_change(
    body: PasswordChangeBody,
    request: Request,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    authorization: Optional[str] = Header(None),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.effective_auth_rate_limit, cfg.auth_rate_window_sec)
    token = extract_token(authorization)
    try:
        return change_account_password(
            conn,
            user_id,
            current_password=body.current_password,
            new_password=body.new_password,
            confirm_password=body.confirm_password,
            revoke_others=body.revoke_other_sessions,
            keep_token=token,
        )
    except Exception as e:
        _raise(e)


@router.get("/activity")
def security_activity(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    return {"items": list_security_events(conn, user_id)}
