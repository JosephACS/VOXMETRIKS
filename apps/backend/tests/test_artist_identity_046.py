"""Spec 046 — Artist Space isolation & membership API tests (A–K)."""

from __future__ import annotations

from datetime import timedelta

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.time_util import utc_now
from app.packages.artists.identity_access.errors import (
    InvitationAlreadyUsed,
    InvitationExpired,
    PermissionDenied,
    ValidationError,
)
from app.packages.artists.identity_access.use_cases import (
    ArtistAccessRequestUseCases,
    ArtistSpaceUseCases,
    PlatformArtistRequestUseCases,
    _create_membership,
    _create_profile,
)
from app.packages.organizations.domain.invitation_token import hash_invitation_token


@pytest.fixture()
def identity_conn(tmp_path):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path / "artist_identity.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_artista (
            id_artista INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY,
            nombre_track VARCHAR NOT NULL,
            id_artista INTEGER,
            duration_ms INTEGER
        )
    """)
    conn.execute(
        "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (101, 'Warehouse One'), (102, 'Warehouse Two')"
    )
    conn.execute(
        "INSERT INTO dim_track (id_track, nombre_track, id_artista, duration_ms) VALUES (1, 'Song A', 101, 180000)"
    )

    ensure_artist_tables(conn)

    # Extra isolation user (invitee)
    now = utc_now()
    if not conn.execute(
        "SELECT 1 FROM app_user WHERE LOWER(email) = ?", ["other046@example.com"]
    ).fetchone():
        nid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_user").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, created_at, preferences_json)
            VALUES (?, 'other046', 'other046@example.com', 'x', 'user', 'free', ?, '{}')
            """,
            [nid, now],
        )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def _uid(conn: duckdb.DuckDBPyConnection, username: str) -> int:
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(username) = ?", [username.lower()]
    ).fetchone()
    assert row, f"user {username} missing"
    return int(row[0])


def _uid_email(conn: duckdb.DuckDBPyConnection, email: str) -> int:
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ?", [email.lower()]
    ).fetchone()
    assert row, f"user {email} missing"
    return int(row[0])


def _profile_with_owner(conn, *, owner_id: int, warehouse_id=101, org_id=0):
    profile = _create_profile(
        conn,
        display_name="Test Artist",
        organization_id=org_id,
        warehouse_artist_id=warehouse_id,
        created_by=owner_id,
    )
    membership = _create_membership(
        conn, artist_profile_id=profile["id"], user_id=owner_id, role="owner"
    )
    return profile, membership


def test_A_mine_empty(identity_conn):
    assert ArtistSpaceUseCases(identity_conn).list_mine(_uid(identity_conn, "demo")) == []


def test_B_mine_one(identity_conn):
    demo = _uid(identity_conn, "demo")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    items = ArtistSpaceUseCases(identity_conn).list_mine(demo)
    assert len(items) == 1
    assert items[0]["artist_profile_id"] == profile["id"]
    assert items[0]["membership_role"] == "owner"
    assert "artist_space.view" in items[0]["permissions"]
    assert items[0]["organization_id"] == 0


def test_C_mine_many(identity_conn):
    demo = _uid(identity_conn, "demo")
    p1, _ = _profile_with_owner(identity_conn, owner_id=demo, warehouse_id=101)
    p2 = _create_profile(
        identity_conn,
        display_name="Second",
        organization_id=0,
        warehouse_artist_id=102,
        created_by=demo,
    )
    _create_membership(identity_conn, artist_profile_id=p2["id"], user_id=demo, role="member")
    items = ArtistSpaceUseCases(identity_conn).list_mine(demo)
    assert len(items) == 2
    assert {i["artist_profile_id"] for i in items} == {p1["id"], p2["id"]}


def test_D_revoked_disappears(identity_conn):
    demo = _uid(identity_conn, "demo")
    other = _uid_email(identity_conn, "other046@example.com")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    m2 = _create_membership(
        identity_conn, artist_profile_id=profile["id"], user_id=other, role="member"
    )
    assert len(ArtistSpaceUseCases(identity_conn).list_mine(other)) == 1
    ArtistSpaceUseCases(identity_conn).revoke_member(
        artist_profile_id=profile["id"], user_id=demo, membership_id=m2["id"]
    )
    assert ArtistSpaceUseCases(identity_conn).list_mine(other) == []


def test_E_user_a_isolation_from_b(identity_conn):
    demo = _uid(identity_conn, "demo")
    other = _uid_email(identity_conn, "other046@example.com")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    assert ArtistSpaceUseCases(identity_conn).list_mine(other) == []
    with pytest.raises(PermissionDenied):
        ArtistSpaceUseCases(identity_conn).summary(
            artist_profile_id=profile["id"], user_id=other
        )


def test_F_pending_claim_no_membership(identity_conn):
    demo = _uid(identity_conn, "demo")
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=demo, request_type="claim_ownership", warehouse_artist_id=101
    )
    assert req["status"] == "pending"
    assert ArtistSpaceUseCases(identity_conn).list_mine(demo) == []


def test_G_approve_creates_membership(identity_conn):
    demo = _uid(identity_conn, "demo")
    admin = _uid(identity_conn, "admin")
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=demo, request_type="claim_ownership", warehouse_artist_id=101
    )
    result = PlatformArtistRequestUseCases(identity_conn).approve(
        user_id=admin, request_id=req["id"]
    )
    assert result["reviewer_became_member"] is False
    items = ArtistSpaceUseCases(identity_conn).list_mine(demo)
    assert len(items) == 1
    assert items[0]["membership_role"] == "owner"
    assert ArtistSpaceUseCases(identity_conn).list_mine(admin) == []
    summary = ArtistSpaceUseCases(identity_conn).summary(
        artist_profile_id=items[0]["artist_profile_id"], user_id=demo
    )
    assert summary["track_count"] == 1


def test_H_reject_no_membership(identity_conn):
    demo = _uid(identity_conn, "demo")
    admin = _uid(identity_conn, "admin")
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=demo, request_type="claim_ownership", warehouse_artist_id=101
    )
    PlatformArtistRequestUseCases(identity_conn).reject(
        user_id=admin, request_id=req["id"], reason="nope"
    )
    assert ArtistSpaceUseCases(identity_conn).list_mine(demo) == []


def test_I_invite_expired_revoked_one_time(identity_conn):
    demo = _uid(identity_conn, "demo")
    other = _uid_email(identity_conn, "other046@example.com")
    eng = _uid(identity_conn, "engineer")
    eng_email = identity_conn.execute(
        "SELECT email FROM app_user WHERE id = ?", [eng]
    ).fetchone()[0]
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)

    invite = ArtistSpaceUseCases(identity_conn).create_invitation(
        artist_profile_id=profile["id"],
        user_id=demo,
        email="other046@example.com",
        role="member",
    )
    token = invite["invite_token"]
    ArtistSpaceUseCases(identity_conn).accept_invitation(user_id=other, raw_token=token)
    assert len(ArtistSpaceUseCases(identity_conn).list_mine(other)) == 1
    with pytest.raises(InvitationAlreadyUsed):
        ArtistSpaceUseCases(identity_conn).accept_invitation(user_id=other, raw_token=token)

    invite2 = ArtistSpaceUseCases(identity_conn).create_invitation(
        artist_profile_id=profile["id"],
        user_id=demo,
        email=str(eng_email),
        role="reader",
    )
    th = hash_invitation_token(invite2["invite_token"])
    row = identity_conn.execute(
        "SELECT id, artist_profile_id, email_normalized, token_hash, role, invited_by, created_at "
        "FROM app_artist_invitation WHERE token_hash = ?",
        [th],
    ).fetchone()
    past = utc_now() - timedelta(days=1)
    identity_conn.execute("DELETE FROM app_artist_invitation WHERE id = ?", [int(row[0])])
    identity_conn.execute(
        """
        INSERT INTO app_artist_invitation
            (id, artist_profile_id, email_normalized, token_hash, role, status,
             expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, NULL, NULL, ?, ?)
        """,
        [
            int(row[0]),
            int(row[1]),
            str(row[2]),
            str(row[3]),
            str(row[4]),
            past,
            int(row[5]),
            row[6],
            past,
        ],
    )
    with pytest.raises(InvitationExpired):
        ArtistSpaceUseCases(identity_conn).accept_invitation(
            user_id=eng, raw_token=invite2["invite_token"]
        )


def test_J_member_cannot_grant_owner(identity_conn):
    demo = _uid(identity_conn, "demo")
    other = _uid_email(identity_conn, "other046@example.com")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    m2 = _create_membership(
        identity_conn, artist_profile_id=profile["id"], user_id=other, role="member"
    )
    with pytest.raises(ValidationError):
        ArtistSpaceUseCases(identity_conn).change_role(
            artist_profile_id=profile["id"],
            user_id=demo,
            membership_id=m2["id"],
            new_role="owner",
        )
    with pytest.raises(ValidationError):
        ArtistSpaceUseCases(identity_conn).create_invitation(
            artist_profile_id=profile["id"],
            user_id=demo,
            email="x046@example.com",
            role="owner",
        )


def test_K_engineer_identity_no_artist_access(identity_conn):
    demo = _uid(identity_conn, "demo")
    eng = _uid(identity_conn, "engineer")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    assert ArtistSpaceUseCases(identity_conn).list_mine(eng) == []
    with pytest.raises(PermissionDenied):
        ArtistSpaceUseCases(identity_conn).get_profile(
            artist_profile_id=profile["id"], user_id=eng
        )


def test_L_platform_admin_review_without_becoming_member(identity_conn):
    demo = _uid(identity_conn, "demo")
    admin = _uid(identity_conn, "admin")
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=demo,
        request_type="create_new",
        proposed_display_name="Brand New Act",
    )
    result = PlatformArtistRequestUseCases(identity_conn).approve(
        user_id=admin, request_id=req["id"]
    )
    assert result["reviewer_became_member"] is False
    assert ArtistSpaceUseCases(identity_conn).list_mine(admin) == []
    assert len(ArtistSpaceUseCases(identity_conn).list_mine(demo)) == 1


def test_create_new_independent_org_id_zero(identity_conn):
    other = _uid_email(identity_conn, "other046@example.com")
    admin = _uid(identity_conn, "admin")
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=other,
        request_type="create_new",
        proposed_display_name="Indie Solo",
    )
    PlatformArtistRequestUseCases(identity_conn).approve(user_id=admin, request_id=req["id"])
    items = ArtistSpaceUseCases(identity_conn).list_mine(other)
    assert items[0]["organization_id"] == 0


def test_request_access_owner_approves(identity_conn):
    demo = _uid(identity_conn, "demo")
    other = _uid_email(identity_conn, "other046@example.com")
    profile, _ = _profile_with_owner(identity_conn, owner_id=demo)
    req = ArtistAccessRequestUseCases(identity_conn).create(
        user_id=other,
        request_type="request_access",
        target_artist_profile_id=profile["id"],
        proposed_role="reader",
    )
    ArtistSpaceUseCases(identity_conn).approve_access_request(
        artist_profile_id=profile["id"], user_id=demo, request_id=req["id"]
    )
    items = ArtistSpaceUseCases(identity_conn).list_mine(other)
    assert len(items) == 1
    assert items[0]["membership_role"] == "reader"


def test_schema_tables_exist(identity_conn):
    for table in (
        "app_artist_membership",
        "app_artist_access_request",
        "app_artist_invitation",
    ):
        identity_conn.execute(f"SELECT id FROM {table} LIMIT 0")


def test_api_mine_auth_required(client: TestClient):
    assert client.get("/api/v1/artist-space/mine").status_code == 401


def test_api_mine_empty(client: TestClient, auth_headers: dict):
    resp = client.get("/api/v1/artist-space/mine", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)
