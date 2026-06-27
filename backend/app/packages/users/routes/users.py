"""Users API — login, register, profile, preferences."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.core.database import get_conn, get_write_conn
from app.core.config import get_settings
from app.core.rate_limit import check_auth_rate_limit
from app.shared.schemas.models import (
    UserLogin, UserRegister, UserProfile, UserPublic, UserPreferencesUpdate,
    VerifyEmailRequest, ResendCodeRequest, GoogleLoginRequest, AuthConfig,
)
from app.packages.users.services.auth_deps import require_user_id, extract_token
from app.packages.users.services.user_service import (
    login, register, get_me, update_preferences, logout,
    verify_email, resend_verification, google_login,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/auth-config", response_model=AuthConfig, summary="Public auth configuration")
def auth_config():
    cfg = get_settings()
    return AuthConfig(
        google_client_id=cfg.google_client_id.strip(),
        email_verification_enabled=True,
    )


@router.post("/login", summary="Login with email/username and password")
def login_user(
    body: UserLogin,
    request: Request,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.auth_rate_limit, cfg.auth_rate_window_sec)
    result = login(conn, body.login, body.password, remember=body.remember)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if result.get("verification_required"):
        raise HTTPException(
            status_code=403,
            detail={"reason": "email_not_verified", "email": result.get("email")},
        )
    return result


@router.post("/register", status_code=201, summary="Register new user (sends email code)")
def register_user(
    body: UserRegister,
    request: Request,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return register(
            conn, body.username, body.email, body.password, body.favorite_genre
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/verify-email", summary="Confirm sign-up with the emailed code")
def verify_email_route(
    body: VerifyEmailRequest,
    request: Request,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        result = verify_email(conn, body.email, body.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=400, detail="verification failed")
    return result


@router.post("/resend-code", summary="Resend the email verification code")
def resend_code_route(
    body: ResendCodeRequest,
    request: Request,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.auth_rate_limit, cfg.auth_rate_window_sec)
    try:
        return resend_verification(conn, body.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/google", summary="Login or register with a Google ID token")
def google_login_route(
    body: GoogleLoginRequest,
    request: Request,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    cfg = get_settings()
    check_auth_rate_limit(request, cfg.auth_rate_limit, cfg.auth_rate_window_sec)
    result = google_login(conn, body.credential)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid Google credential")
    return result


@router.post("/logout", summary="Invalidate current session token")
def logout_user(
    authorization: Optional[str] = Header(None),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    token = extract_token(authorization)
    if token:
        logout(conn, token)
    return {"ok": True}


@router.get("/me", response_model=UserProfile, summary="Current user profile")
def me(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    profile = get_me(conn, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.patch("/me/preferences", response_model=UserPublic, summary="Update preferences")
def patch_preferences(
    body: UserPreferencesUpdate,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    updates = body.model_dump(exclude_unset=True)
    user = update_preferences(conn, user_id, updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
