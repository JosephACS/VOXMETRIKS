"""Spec 051 T003 — artist publishing RBAC, cross-artist isolation, platform review.

Runs against the shared pytest TestClient database (a temp DuckDB created by
conftest); the canonical warehouse is never opened. Media uploads are avoided on
purpose: the permission boundary is asserted before any release becomes ready,
so these tests never write audio or cover files.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.artists.identity_access import ARTIST_WORKSPACE_TYPE
from app.packages.artists.identity_access.use_cases import (
    _create_membership,
    _create_profile,
)
from app.packages.artists.identity_access.workspace_provisioning import (
    provision_artist_workspace,
)
from app.packages.catalog_publishing.application.use_cases import (
    CatalogPublishingUseCases,
)
from app.packages.catalog_publishing.domain.state_machine import transition
from app.packages.identity.services.password_security import hash_password
from app.packages.organizations.domain.enums import OrganizationStatus
from app.packages.organizations.infrastructure.repositories import OrganizationRepository

PASSWORD = "Spec051-Str0ng!"
ROLES = ("owner", "administrator", "member", "reader", "outsider")
TAG = "s051"


def _seed_user(username: str) -> int:
    """Verified local user, created directly so login needs no e-mail round trip."""
    with using_write_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM app_user WHERE username = ?", [username]
        ).fetchone()
        if existing:
            return int(existing[0])
        user_id = int(
            conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_user").fetchone()[0]
        )
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre,
                 created_at, preferences_json, email_verified, auth_provider)
            VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, '{}', TRUE, 'local')
            """,
            [
                user_id,
                username,
                f"{username}@voxmetrik.io",
                hash_password(PASSWORD),
                utc_now(),
            ],
        )
    return user_id


def _login(client: TestClient, username: str) -> tuple[int, dict[str, str]]:
    user_id = _seed_user(username)
    login = client.post(
        "/api/v1/users/login",
        json={"login": username, "password": PASSWORD, "remember": True},
    )
    assert login.status_code == 200, login.text
    return user_id, {"Authorization": f"Bearer {login.json()['token']}"}


@pytest.fixture(scope="module")
def space(client: TestClient) -> dict:
    """Two independent artists plus one ordinary label organization."""
    tag = TAG
    users = {role: _login(client, f"s051_{role}") for role in ROLES}

    with using_write_conn() as conn:
        primary_org = provision_artist_workspace(
            conn,
            display_name=f"Spec051 Primary {tag}",
            owner_user_id=users["owner"][0],
            seed_key=f"test:primary:{tag}",
        ).organization_id
        primary = _create_profile(
            conn,
            display_name=f"Spec051 Primary {tag}",
            organization_id=primary_org,
            warehouse_artist_id=None,
            created_by=users["owner"][0],
        )
        _create_membership(
            conn,
            artist_profile_id=primary["id"],
            user_id=users["owner"][0],
            role="owner",
        )
        for role in ("administrator", "member", "reader"):
            _create_membership(
                conn,
                artist_profile_id=primary["id"],
                user_id=users[role][0],
                role=role,
            )

        other_org = provision_artist_workspace(
            conn,
            display_name=f"Spec051 Other {tag}",
            owner_user_id=users["outsider"][0],
            seed_key=f"test:other:{tag}",
        ).organization_id
        other = _create_profile(
            conn,
            display_name=f"Spec051 Other {tag}",
            organization_id=other_org,
            warehouse_artist_id=None,
            created_by=users["outsider"][0],
        )
        _create_membership(
            conn,
            artist_profile_id=other["id"],
            user_id=users["outsider"][0],
            role="owner",
        )

        label = OrganizationRepository(conn).create(
            display_name=f"Spec051 Label {tag}",
            slug=f"spec051-label-{tag}",
            organization_type="label",
            created_by=users["owner"][0],
            status=OrganizationStatus.ACTIVE.value,
        )

    return {
        "users": users,
        "primary_id": int(primary["id"]),
        "primary_org": int(primary_org),
        "other_id": int(other["id"]),
        "other_org": int(other_org),
        "label_org": int(label.id),
    }


def _headers(space: dict, role: str) -> dict[str, str]:
    return space["users"][role][1]


def _user_id(space: dict, role: str) -> int:
    return space["users"][role][0]


def _base(artist_profile_id: int) -> str:
    return f"/api/v1/artist-space/{artist_profile_id}/publishing"


def _code(response) -> str:
    """Stable error code, whichever envelope the app applied."""
    body = response.json()
    payload = body.get("details") or body.get("detail") or {}
    return str(payload.get("code") or "")


def _create_release(client: TestClient, space: dict, role: str, title: str):
    return client.post(
        f"{_base(space['primary_id'])}/releases",
        json={"title": title},
        headers=_headers(space, role),
    )


# ── artist publishing RBAC ─────────────────────────────────────────────────


def test_publishing_requires_authentication(client: TestClient, space: dict) -> None:
    assert client.get(f"{_base(space['primary_id'])}/releases").status_code == 401


@pytest.mark.parametrize("role", ["owner", "administrator", "member", "reader"])
def test_every_member_role_can_read_the_catalog(
    client: TestClient, space: dict, role: str
) -> None:
    resp = client.get(
        f"{_base(space['primary_id'])}/releases", headers=_headers(space, role)
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


@pytest.mark.parametrize("role", ["owner", "administrator", "member"])
def test_create_and_edit_roles_can_draft_releases(
    client: TestClient, space: dict, role: str
) -> None:
    created = _create_release(client, space, role, f"Draft by {role}")
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "draft"
    assert int(body["organization_id"]) == space["primary_org"]
    assert int(body["artist_profile_id"]) == space["primary_id"]

    patched = client.patch(
        f"{_base(space['primary_id'])}/releases/{body['id']}",
        json={"title": f"Renamed by {role}"},
        headers=_headers(space, role),
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["title"] == f"Renamed by {role}"


def test_reader_cannot_create_or_edit(client: TestClient, space: dict) -> None:
    denied = _create_release(client, space, "reader", "Reader draft")
    assert denied.status_code == 403, denied.text
    assert _code(denied) == "permission_denied"

    owned = _create_release(client, space, "owner", "Owner draft for reader")
    assert owned.status_code == 201, owned.text
    submission_id = owned.json()["id"]

    patched = client.patch(
        f"{_base(space['primary_id'])}/releases/{submission_id}",
        json={"genre": "rock"},
        headers=_headers(space, "reader"),
    )
    assert patched.status_code == 403
    tracks = client.post(
        f"{_base(space['primary_id'])}/releases/{submission_id}/tracks",
        json={"title": "Nope"},
        headers=_headers(space, "reader"),
    )
    assert tracks.status_code == 403


def test_only_owner_and_administrator_may_submit(
    client: TestClient, space: dict
) -> None:
    created = _create_release(client, space, "member", "Submit boundary")
    assert created.status_code == 201, created.text
    submission_id = created.json()["id"]
    url = f"{_base(space['primary_id'])}/releases/{submission_id}/submit"

    for role in ("member", "reader"):
        denied = client.post(url, headers=_headers(space, role))
        assert denied.status_code == 403, f"{role}: {denied.text}"

    # Owner/administrator clear RBAC; the draft is still blocked on readiness,
    # which is a validation failure, never a permission failure.
    for role in ("owner", "administrator"):
        allowed = client.post(url, headers=_headers(space, role))
        assert allowed.status_code == 422, f"{role}: {allowed.text}"
        assert _code(allowed) == "validation_error"
        assert "missing_cover" in allowed.text


def test_validate_reports_blockers_for_readers(client: TestClient, space: dict) -> None:
    created = _create_release(client, space, "owner", "Validate blockers")
    submission_id = created.json()["id"]
    resp = client.post(
        f"{_base(space['primary_id'])}/releases/{submission_id}/validate",
        headers=_headers(space, "reader"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ready"] is False
    assert "no_tracks" in body["blockers"]


# ── cross-artist isolation ─────────────────────────────────────────────────


def test_non_member_is_forbidden_on_another_artist(
    client: TestClient, space: dict
) -> None:
    resp = client.get(
        f"{_base(space['primary_id'])}/releases", headers=_headers(space, "outsider")
    )
    assert resp.status_code == 403, resp.text
    assert _code(resp) == "permission_denied"


def test_release_of_another_artist_is_not_reachable(
    client: TestClient, space: dict
) -> None:
    created = _create_release(client, space, "owner", "Primary only")
    submission_id = created.json()["id"]

    # The outsider owns a different artist: their own space must not expose it.
    resp = client.get(
        f"{_base(space['other_id'])}/releases/{submission_id}",
        headers=_headers(space, "outsider"),
    )
    assert resp.status_code == 404, resp.text

    listed = client.get(
        f"{_base(space['other_id'])}/releases", headers=_headers(space, "outsider")
    )
    assert listed.status_code == 200
    assert submission_id not in [r["id"] for r in listed.json()]


def test_client_supplied_organization_header_is_ignored(
    client: TestClient, space: dict
) -> None:
    headers = {**_headers(space, "owner"), "X-Organization-Id": str(space["label_org"])}
    created = client.post(
        f"{_base(space['primary_id'])}/releases",
        json={"title": "Header spoof"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    assert int(created.json()["organization_id"]) == space["primary_org"]


def test_hidden_workspace_is_not_listed_as_a_space(
    client: TestClient, space: dict
) -> None:
    bootstrap = client.get("/api/v1/session/bootstrap", headers=_headers(space, "owner"))
    assert bootstrap.status_code == 200, bootstrap.text
    keys = [s["key"] for s in bootstrap.json()["spaces"]]
    assert f"organization:{space['primary_org']}" not in keys


# ── platform review queue ──────────────────────────────────────────────────


def _seed_submitted(
    *, organization_id: int, artist_profile_id: int, actor_user_id: int, title: str
) -> int:
    """Create a draft and move it to ``submitted`` without touching media.

    ``created_by`` is the submitter the self-review guard checks, so the actor
    passed here is who the platform reviewer must not be.
    """
    with using_write_conn() as conn:
        draft = CatalogPublishingUseCases(conn).create_draft(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            artist_profile_id=artist_profile_id,
            title=title,
        )
        transition(conn, draft, "submitted", actor_user_id=actor_user_id, reason="seed")
    return int(draft["id"])


def test_platform_queue_requires_platform_admin(
    client: TestClient, space: dict
) -> None:
    denied = client.get(
        "/api/v1/platform/catalog-reviews", headers=_headers(space, "owner")
    )
    assert denied.status_code == 403, denied.text
    assert client.get("/api/v1/platform/catalog-reviews").status_code == 401


def test_platform_queue_only_shows_artist_workspace_submissions(
    client: TestClient, space: dict, admin_auth_headers: dict
) -> None:
    independent = _seed_submitted(
        organization_id=space["primary_org"],
        artist_profile_id=space["primary_id"],
        actor_user_id=_user_id(space, "owner"),
        title="Independent release",
    )
    label_backed = _seed_submitted(
        organization_id=space["label_org"],
        artist_profile_id=space["primary_id"],
        actor_user_id=_user_id(space, "owner"),
        title="Label release",
    )

    listed = client.get("/api/v1/platform/catalog-reviews", headers=admin_auth_headers)
    assert listed.status_code == 200, listed.text
    ids = [r["id"] for r in listed.json()]
    assert independent in ids
    assert label_backed not in ids

    detail = client.get(
        f"/api/v1/platform/catalog-reviews/{independent}", headers=admin_auth_headers
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["submission"]["id"] == independent

    # A label release keeps its organization-scoped review flow.
    hidden = client.get(
        f"/api/v1/platform/catalog-reviews/{label_backed}", headers=admin_auth_headers
    )
    assert hidden.status_code == 404, hidden.text


def test_platform_reviewer_can_request_changes(
    client: TestClient, space: dict, admin_auth_headers: dict
) -> None:
    submission_id = _seed_submitted(
        organization_id=space["primary_org"],
        artist_profile_id=space["primary_id"],
        actor_user_id=_user_id(space, "owner"),
        title="Needs changes",
    )
    resp = client.post(
        f"/api/v1/platform/catalog-reviews/{submission_id}/request-changes",
        json={"notes": "Cover art is too small"},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "changes_requested"

    with using_write_conn() as conn:
        assert int(
            conn.execute(
                "SELECT COUNT(*) FROM app_release_review WHERE submission_id = ?",
                [submission_id],
            ).fetchone()[0]
        ) == 1


def test_platform_reviewer_cannot_approve_their_own_submission(
    client: TestClient, space: dict, admin_auth_headers: dict
) -> None:
    admin_id = int(client.get("/api/v1/users/me", headers=admin_auth_headers).json()["id"])
    submission_id = _seed_submitted(
        organization_id=space["primary_org"],
        artist_profile_id=space["primary_id"],
        actor_user_id=admin_id,
        title="Self review",
    )
    resp = client.post(
        f"/api/v1/platform/catalog-reviews/{submission_id}/approve",
        json={"notes": "looks good to me"},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 403, resp.text
    assert _code(resp) == "self_approve_forbidden"


def test_workspace_organizations_are_typed_as_hidden(space: dict) -> None:
    with using_write_conn() as conn:
        row = conn.execute(
            "SELECT organization_type FROM app_organization WHERE id = ?",
            [space["primary_org"]],
        ).fetchone()
    assert row and row[0] == ARTIST_WORKSPACE_TYPE
