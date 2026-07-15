"""Spec 031 — Catalog publishing golden path + negatives."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import duckdb
import pytest

from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.domain.errors import (
    ConflictError,
    MediaValidationError,
    NotFoundError,
    RightsGateError,
    SelfApproveError,
)
from app.packages.catalog_publishing.infrastructure.local_media_storage import (
    LocalMediaStorageProvider,
    make_minimal_png,
    make_minimal_wav,
)
from app.packages.catalog_publishing.infrastructure.schema import (
    DEMO_WAREHOUSE_TRACK_ID_MIN,
    ensure_catalog_publishing_tables,
)
from app.packages.streaming.services.audio_source_service import get_audio_source_response

ARTIST = 9310
REVIEWER = 9311
ORG = 9400
OTHER_ORG = 9401


@pytest.fixture()
def pub_db(tmp_path, monkeypatch):
    from app.core import schema_bootstrap
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables

    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setenv("MEDIA_STORAGE_ROOT", str(media_root))
    monkeypatch.setenv("ALLOW_DEMO_SELF_APPROVE", "0")
    monkeypatch.chdir(tmp_path)

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "publishing_s031.duckdb"))

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_catalog_publishing_tables(conn)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY,
            nombre_track VARCHAR,
            duration_ms INTEGER,
            popularity INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_track_audio_source (
            track_id INTEGER PRIMARY KEY,
            provider VARCHAR NOT NULL DEFAULT 'youtube',
            youtube_video_id VARCHAR,
            source_ref VARCHAR,
            playable_url VARCHAR,
            query VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'ok',
            failure_count INTEGER DEFAULT 0,
            confidence_score DOUBLE,
            resolved_at TIMESTAMP,
            last_checked_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_track_cover (
            track_id INTEGER PRIMARY KEY,
            image_url VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'ok',
            resolved_at TIMESTAMP
        )
        """
    )

    now = utc_now()
    for oid, slug, name in (
        (ORG, "pub-org-s031", "Publishing Org"),
        (OTHER_ORG, "other-org-s031", "Other Org"),
    ):
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?)
            """,
            [oid, name, name, slug, ARTIST, now, now],
        )

    for uid, uname, email in (
        (ARTIST, "pub_artist", "pub_artist@test.local"),
        (REVIEWER, "pub_reviewer", "pub_reviewer@test.local"),
    ):
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre,
                 created_at, preferences_json, email_verified, auth_provider)
            VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, '{}', TRUE, 'local')
            """,
            [uid, uname, email, hash_password("pass"), now],
        )

    role_ids = {
        r[0]: int(r[1])
        for r in conn.execute("SELECT code, id FROM app_business_role").fetchall()
    }

    def _member(user_id: int, role_code: str, org_id: int = ORG) -> None:
        mid = int(
            conn.execute(
                "SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member"
            ).fetchone()[0]
        )
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, joined_at, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [mid, org_id, user_id, now, ARTIST, now, now],
        )
        mrid = int(
            conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0]
        )
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            [mrid, mid, role_ids[role_code], ARTIST, now],
        )

    _member(ARTIST, "artist_manager")
    _member(REVIEWER, "owner")

    # Artist profile
    conn.execute(
        """
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name,
             status, warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (1, ?, 'Pub Artist', NULL, 'pub artist', 'active', NULL, ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_artist_portal_access
            (id, user_id, artist_profile_id, organization_id, status, created_at)
        VALUES (1, ?, 1, ?, 'active', ?)
        """,
        [ARTIST, ORG, now],
    )

    # Good 60/40 contract
    conn.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id,
             artist_profile_id, created_by, created_at, updated_at)
        VALUES (1, ?, 'Asset One', 'active', NULL, 1, ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract
            (id, organization_id, asset_id, rights_type, status, exclusive,
             valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
        VALUES (1, ?, 1, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract_party
            (id, contract_id, party_name, party_type, ownership_percentage,
             organization_id, artist_profile_id, created_at, updated_at)
        VALUES
            (1, 1, 'A', 'external', 60, NULL, NULL, ?, ?),
            (2, 1, 'B', 'external', 40, NULL, NULL, ?, ?)
        """,
        [now, now, now, now],
    )

    # Bad 90% contract
    conn.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id,
             artist_profile_id, created_by, created_at, updated_at)
        VALUES (2, ?, 'Asset Bad', 'active', NULL, 1, ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract
            (id, organization_id, asset_id, rights_type, status, exclusive,
             valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
        VALUES (2, ?, 2, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract_party
            (id, contract_id, party_name, party_type, ownership_percentage,
             organization_id, artist_profile_id, created_at, updated_at)
        VALUES (3, 2, 'Solo', 'external', 90, NULL, NULL, ?, ?)
        """,
        [now, now],
    )

    media = LocalMediaStorageProvider(root=media_root)
    uc = CatalogPublishingUseCases(conn, media=media)
    yield conn, uc, media_root
    conn.close()
    schema_bootstrap._schema_ready = previous


def _ready_submission(uc, *, title="Song", contract_id=1, catalog_asset_id=1):
    wav = make_minimal_wav()
    png = make_minimal_png(512, 512)
    draft = uc.create_draft(
        actor_user_id=ARTIST,
        organization_id=ORG,
        artist_profile_id=1,
        title=title,
        rights_contract_id=contract_id,
        planned_release_date=date(2026, 7, 1),
        is_demo=False,
    )
    tr = uc.add_track(
        submission_id=draft["id"], organization_id=ORG, title=f"{title} Track"
    )
    uc.upload_audio(
        submission_id=draft["id"],
        track_id=tr["id"],
        organization_id=ORG,
        actor_user_id=ARTIST,
        filename="t.wav",
        content_type="audio/wav",
        data=wav,
    )
    uc.upload_cover(
        submission_id=draft["id"],
        organization_id=ORG,
        actor_user_id=ARTIST,
        filename="c.png",
        content_type="image/png",
        data=png,
    )
    # Link asset for rights gate conflict lookups
    uc._conn.execute(
        """
        UPDATE app_release_submission_track
        SET catalog_asset_id = ?, rights_contract_id = ?
        WHERE id = ?
        """,
        [catalog_asset_id, contract_id, tr["id"]],
    )
    return draft["id"], tr["id"]


def test_happy_path_publish_and_local_published_priority(pub_db):
    conn, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="Happy")
    uc.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    uc.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)
    result = uc.publish(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        idempotency_key="pub-happy-1",
    )
    assert result["submission"]["status"] == "published"
    wtid = result["warehouse_track_ids"][0]
    assert wtid >= DEMO_WAREHOUSE_TRACK_ID_MIN or wtid is not None
    src = get_audio_source_response(conn, wtid, force=True, async_resolve=False)
    assert src is not None
    assert src["provider"] == "local_published"
    assert src["status"] == "ok"
    assert "/api/v1/media/" in (src.get("playable_url") or "")


def test_no_audio_blocks_submit(pub_db):
    _, uc, _ = pub_db
    draft = uc.create_draft(
        actor_user_id=ARTIST,
        organization_id=ORG,
        artist_profile_id=1,
        title="No Audio",
    )
    uc.add_track(submission_id=draft["id"], organization_id=ORG, title="T")
    with pytest.raises(Exception) as ei:
        uc.submit(submission_id=draft["id"], organization_id=ORG, actor_user_id=ARTIST)
    assert "missing_audio" in str(ei.value) or "not ready" in str(ei.value).lower()


def test_bad_mime_and_path_traversal(pub_db):
    _, uc, _ = pub_db
    draft = uc.create_draft(
        actor_user_id=ARTIST,
        organization_id=ORG,
        artist_profile_id=1,
        title="Bad Media",
    )
    tr = uc.add_track(submission_id=draft["id"], organization_id=ORG, title="T")
    with pytest.raises(MediaValidationError):
        uc.upload_audio(
            submission_id=draft["id"],
            track_id=tr["id"],
            organization_id=ORG,
            actor_user_id=ARTIST,
            filename="evil.exe",
            content_type="application/x-msdownload",
            data=b"MZ\x90\x00not-audio",
        )
    with pytest.raises(MediaValidationError):
        uc.upload_audio(
            submission_id=draft["id"],
            track_id=tr["id"],
            organization_id=ORG,
            actor_user_id=ARTIST,
            filename="../evil.wav",
            content_type="audio/wav",
            data=make_minimal_wav(),
        )


def test_duplicate_hash_blocks(pub_db):
    _, uc, _ = pub_db
    wav = make_minimal_wav()
    sid1, tid1 = _ready_submission(uc, title="Dup1")
    # Second submission same hash
    draft = uc.create_draft(
        actor_user_id=ARTIST,
        organization_id=ORG,
        artist_profile_id=1,
        title="Dup2",
    )
    tr = uc.add_track(submission_id=draft["id"], organization_id=ORG, title="T2")
    with pytest.raises(ConflictError):
        uc.upload_audio(
            submission_id=draft["id"],
            track_id=tr["id"],
            organization_id=ORG,
            actor_user_id=ARTIST,
            filename="same.wav",
            content_type="audio/wav",
            data=wav,
        )


def test_ownership_90_blocks_approve(pub_db):
    _, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="BadPct", contract_id=2, catalog_asset_id=2)
    uc.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    with pytest.raises(RightsGateError):
        uc.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)


def test_self_approve_blocked(pub_db):
    _, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="Self")
    uc.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    with pytest.raises(SelfApproveError):
        uc.approve(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)


def test_wrong_org_not_found(pub_db):
    _, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="OrgIso")
    with pytest.raises(NotFoundError):
        uc.get_detail(submission_id=sid, organization_id=OTHER_ORG)


def test_publish_idempotent(pub_db):
    _, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="Idem")
    uc.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    uc.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)
    a = uc.publish(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        idempotency_key="idem-1",
    )
    b = uc.publish(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        idempotency_key="idem-1",
    )
    assert a["publication_id"] == b["publication_id"]
    assert b["idempotent"] is True


def test_suspend_disables_local_published(pub_db):
    conn, uc, _ = pub_db
    sid, _ = _ready_submission(uc, title="Sus")
    uc.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    uc.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)
    pub = uc.publish(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        idempotency_key="sus-1",
    )
    wtid = pub["warehouse_track_ids"][0]
    uc.suspend(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        reason="takedown demo",
    )
    src = get_audio_source_response(conn, wtid, force=False, async_resolve=False)
    assert src is not None
    assert src["provider"] == "local_published"
    assert src["status"] == "disabled"


def test_schema_tables_exist(pub_db):
    conn, _, _ = pub_db
    from app.packages.catalog_publishing.infrastructure.schema import (
        CATALOG_PUBLISHING_TABLES,
    )

    for t in CATALOG_PUBLISHING_TABLES:
        row = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?", [t]
        ).fetchone()
        assert row, f"missing {t}"
