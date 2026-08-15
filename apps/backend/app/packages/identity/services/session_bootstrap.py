"""Authoritative session bootstrap and explicit space activation (Spec 050).

Composes existing identity / org / artist / platform / household services.
Does not duplicate domain SQL and never grants roles from user input.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb

from datetime import datetime, timedelta, timezone

from app.core.database import transactional
from app.core.logging import get_logger
from app.packages.artists.identity_access.use_cases import ArtistSpaceUseCases
from app.packages.identity.services.profile_security import get_pin_status
from app.packages.identity.services.user_storage import ensure_user_tables, parse_preferences
from app.packages.organizations.domain.enums import (
    HIDDEN_ORGANIZATION_TYPES,
    OrganizationStatus,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)
from app.packages.platform_rbac.infrastructure.repository import list_user_platform_roles

logger = get_logger("voxmetrik.identity.session")

PREF_ACTIVE_SPACE = "active_space_key"
PREF_FIRST_ACCESS = "first_access_completed"

_ORG_BLOCKED = frozenset(
    {
        OrganizationStatus.SUSPENDED_BY_PLATFORM.value,
        OrganizationStatus.CLOSED.value,
        OrganizationStatus.PROVISIONING.value,
    }
)

REASON_MEMBERSHIP = "membership_required"
REASON_ROLE = "role_required"
REASON_TIER = "subscription_tier"
REASON_LIFECYCLE = "lifecycle_blocked"


class SessionContextError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def _cap(code: str, allowed: bool, reason: Optional[str] = None) -> dict[str, Any]:
    return {"code": code, "allowed": bool(allowed), "reason": None if allowed else reason}


def _space(
    *,
    key: str,
    kind: str,
    display_name: str,
    home_path: str,
    capabilities: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "key": key,
        "kind": kind,
        "display_name": display_name,
        "capabilities": capabilities,
        "home_path": home_path,
    }


def provision_free_personal_plan(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[str]:
    """Idempotent Free assignment. Returns a pending-action code on failure."""
    try:
        from app.packages.personal_subscriptions.application.use_cases import (
            ensure_free_subscription,
        )

        ensure_free_subscription(conn, user_id)
        return None
    except Exception:  # noqa: BLE001
        logger.exception("explicit Free provisioning failed for user_id=%s", user_id)
        return "personal_plan_unprovisioned"


def _has_personal_plan(conn: duckdb.DuckDBPyConnection, user_id: int) -> bool:
    try:
        row = conn.execute(
            """
            SELECT 1 FROM personal_subscription
            WHERE user_id = ? AND status IN ('active', 'past_due', 'processing')
            LIMIT 1
            """,
            [user_id],
        ).fetchone()
        return bool(row)
    except Exception:  # noqa: BLE001
        return False


def _prefs(user: dict[str, Any]) -> dict[str, Any]:
    raw = user.get("preferences") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _write_pref(conn: duckdb.DuckDBPyConnection, user_id: int, key: str, value: Any) -> None:
    """Persist a preference key. Caller must hold ``transactional()`` when atomicity matters."""
    row = conn.execute("SELECT preferences_json FROM app_user WHERE id = ?", [user_id]).fetchone()
    prefs = parse_preferences(row[0] if row else "{}")
    prefs[key] = value
    conn.execute(
        "UPDATE app_user SET preferences_json = ? WHERE id = ?",
        [json.dumps(prefs), user_id],
    )


def _space_is_enterable(space: dict[str, Any]) -> bool:
    return any(c.get("allowed") for c in space.get("capabilities") or [])


def _discover_spaces(
    conn: duckdb.DuckDBPyConnection,
    user: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    user_id = int(user["id"])
    role = (user.get("role") or "user").lower()
    pending: list[dict[str, str]] = []
    spaces: list[dict[str, Any]] = [
        _space(
            key="personal",
            kind="personal",
            display_name="Personal",
            home_path="/discover",
            capabilities=[_cap("music.listen", True)],
        )
    ]

    try:
        orgs = OrganizationRepository(conn).list_for_user(user_id)
        for org in orgs:
            if org.organization_type in HIDDEN_ORGANIZATION_TYPES:
                # Hidden artist-workspace tenants are reachable only as artist spaces.
                continue
            allowed = org.status not in _ORG_BLOCKED
            spaces.append(
                _space(
                    key=f"organization:{org.id}",
                    kind="organization",
                    display_name=org.display_name,
                    home_path=f"/organizations/{org.id}",
                    capabilities=[
                        _cap(
                            "organization.view",
                            allowed,
                            REASON_LIFECYCLE if not allowed else None,
                        )
                    ],
                )
            )
    except Exception:  # noqa: BLE001
        logger.exception("organization discovery failed for user_id=%s", user_id)
        pending.append({"code": "organization_discovery_unavailable"})

    try:
        for item in ArtistSpaceUseCases(conn).list_mine(user_id):
            profile_id = int(item.get("artist_profile_id") or item.get("id") or 0)
            if profile_id <= 0:
                continue
            name = str(item.get("display_name") or f"Artist {profile_id}")
            spaces.append(
                _space(
                    key=f"artist:{profile_id}",
                    kind="artist",
                    display_name=name,
                    home_path="/artist-space",
                    capabilities=[_cap("artist_space.view", True)],
                )
            )
    except Exception:  # noqa: BLE001
        logger.exception("artist discovery failed for user_id=%s", user_id)
        pending.append({"code": "artist_discovery_unavailable"})

    if role in {"admin", "engineer"}:
        spaces.append(
            _space(
                key="data_ops",
                kind="data_ops",
                display_name="Data Ops",
                home_path="/workpanel",
                capabilities=[_cap("data_ops.access", True)],
            )
        )

    platform_roles: list[str] = []
    try:
        platform_roles = list_user_platform_roles(conn, user_id)
    except Exception:  # noqa: BLE001
        logger.exception("platform role discovery failed for user_id=%s", user_id)
        pending.append({"code": "platform_discovery_unavailable"})

    if role == "admin" or "platform_admin" in platform_roles:
        spaces.append(
            _space(
                key="platform_admin",
                kind="platform_admin",
                display_name="Platform administration",
                home_path="/workpanel",
                capabilities=[_cap("platform.admin", True)],
            )
        )

    # Keep lifecycle-blocked spaces discoverable so POST /context can return 409.
    return spaces, pending


def _eligible_keys(spaces: list[dict[str, Any]]) -> set[str]:
    return {str(s["key"]) for s in spaces if _space_is_enterable(s)}


def _known_keys(spaces: list[dict[str, Any]]) -> set[str]:
    return {str(s["key"]) for s in spaces}


def _home_for(spaces: list[dict[str, Any]], key: str) -> str:
    for s in spaces:
        if s["key"] == key:
            return str(s["home_path"])
    return "/discover"


def build_session_bootstrap(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    persist_active: Optional[str] = None,
) -> dict[str, Any]:
    ensure_user_tables(conn)
    from app.packages.identity.services.user_service import _fetch_user  # circular: login → provision

    user = _fetch_user(conn, user_id)
    if not user:
        raise SessionContextError("Not authenticated", status_code=401)

    pending: list[dict[str, str]] = []
    if not _has_personal_plan(conn, user_id):
        code = provision_free_personal_plan(conn, user_id)
        if code:
            pending.append({"code": code})

    spaces, discovery_pending = _discover_spaces(conn, user)
    pending.extend(discovery_pending)
    enterable = _eligible_keys(spaces)

    prefs = _prefs(user)
    requested = persist_active or prefs.get(PREF_ACTIVE_SPACE) or "personal"
    if requested not in enterable:
        requested = "personal" if "personal" in enterable else next(iter(enterable), "personal")
    if persist_active is None and not prefs.get(PREF_ACTIVE_SPACE):
        role = (user.get("role") or "user").lower()
        if role == "engineer" and "data_ops" in enterable:
            requested = "data_ops"
        elif role == "admin":
            org_key = next((k for k in enterable if k.startswith("organization:")), None)
            requested = org_key or (
                "platform_admin" if "platform_admin" in enterable else requested
            )

    if persist_active and persist_active in enterable:
        with transactional(conn):
            _write_pref(conn, user_id, PREF_ACTIVE_SPACE, persist_active)
        requested = persist_active
        user = _fetch_user(conn, user_id) or user
        prefs = _prefs(user)

    pin_enabled = False
    try:
        pin_enabled = bool(get_pin_status(conn, user_id).get("enabled"))
    except Exception:  # noqa: BLE001
        pin_enabled = False

    role = (user.get("role") or "user").lower()
    if (
        role == "user"
        and not prefs.get(PREF_FIRST_ACCESS)
        and _account_is_new(user)
        and enterable <= {"personal"}
    ):
        pending.append({"code": "first_run"})
    if (
        role == "user"
        and len(enterable) > 1
        and not prefs.get(PREF_ACTIVE_SPACE)
        and persist_active is None
    ):
        pending.append({"code": "choose_space"})

    return {
        "user": {
            "id": int(user["id"]),
            "display_name": user.get("username") or "User",
            "identity_role": (user.get("role") or "user").lower(),
        },
        "security": {
            "email_verified": bool(user.get("email_verified", True)),
            "profile_pin_enabled": pin_enabled,
        },
        "spaces": spaces,
        "active_space_key": requested,
        "pending_actions": pending,
        "recommended_path": _home_for(spaces, requested),
    }


def activate_session_context(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    space_key: str,
) -> dict[str, Any]:
    raw = (space_key or "").strip()
    if not raw:
        raise SessionContextError("malformed space key", status_code=400)

    kind = raw.split(":", 1)[0]
    if kind not in {"personal", "organization", "artist", "data_ops", "platform_admin"}:
        raise SessionContextError("unsupported space key", status_code=400)
    if kind in {"organization", "artist"}:
        parts = raw.split(":", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            raise SessionContextError("malformed space key", status_code=400)

    ensure_user_tables(conn)
    from app.packages.identity.services.user_service import _fetch_user  # circular: login → provision

    user = _fetch_user(conn, user_id)
    if not user:
        raise SessionContextError("Not authenticated", status_code=401)

    spaces, _ = _discover_spaces(conn, user)
    match = next((s for s in spaces if s["key"] == raw), None)
    if match is None:
        raise SessionContextError("not eligible", status_code=403)

    if not _space_is_enterable(match):
        blocked = [
            c
            for c in match["capabilities"]
            if not c.get("allowed") and c.get("reason") in {REASON_LIFECYCLE, REASON_TIER}
        ]
        if blocked:
            raise SessionContextError("context cannot be activated", status_code=409)
        raise SessionContextError("not eligible", status_code=403)

    return build_session_bootstrap(conn, user_id, persist_active=raw)


def complete_first_access(conn: duckdb.DuckDBPyConnection, user_id: int) -> None:
    with transactional(conn):
        _write_pref(conn, user_id, PREF_FIRST_ACCESS, True)


def _account_is_new(user: dict[str, Any]) -> bool:
    raw = user.get("created_at")
    if not raw:
        return False
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - parsed <= timedelta(hours=48)
    except ValueError:
        return False
