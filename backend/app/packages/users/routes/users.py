"""Users API — login, register, profile, preferences."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_conn, get_write_conn
from app.shared.schemas.models import (
    UserLogin, UserRegister, UserProfile, UserPublic, UserPreferencesUpdate,
)
from app.packages.users.services.auth_deps import require_user_id
from app.packages.users.services.user_service import (
    login, register, get_me, update_preferences,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/login", summary="Login with email/username and password")
def login_user(
    body: UserLogin,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    result = login(conn, body.login, body.password, remember=body.remember)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/register", status_code=201, summary="Register new user")
def register_user(
    body: UserRegister,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return register(
            conn, body.username, body.email, body.password, body.favorite_genre
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
