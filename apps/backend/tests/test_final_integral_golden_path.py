"""Spec 028 global integration / final academic closure.

Pragmatic chain: catalog publish → B2C personal checkout → royalties settlement.
Not Spec 032. EMAIL_PROVIDER=console; no real money.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.domain.errors import RightsGateError, SelfApproveError
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

ARTIST = 9810
REVIEWER = 9811
FINANCE = 9812
LISTENER = 9813
ORG = 9800


@pytest.fixture()
def integral_db(tmp_path, monkeypatch):
    from app.core import schema_bootstrap
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.royalties.infrastructure.schema import ensure_royalty_tables
    from app.packages.engagement.services.app_storage import ensure_app_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables

    monkeypatch.setenv("EMAIL_PROVIDER", "console")
    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setenv("MEDIA_STORAGE_ROOT", str(media_root))
    monkeypatch.setenv("ALLOW_DEMO_SELF_APPROVE", "0")
    monkeypatch.chdir(tmp_path)

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "final_integral.duckdb"))

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_catalog_publishing_tables(conn)
    ensure_royalty_tables(conn)

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
    ensure_app_tables(conn)
    ensure_platform_ops_tables(conn)
    ensure_personal_subscription_tables(conn)

    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at)
        VALUES (?, 'Integral Org', 'Integral Org LLC', 'integral-final-028', 'label',
                'US', 'UTC', 'USD', 'active', ?, ?, ?)
        """,
        [ORG, ARTIST, now, now],
    )
    for uid, uname, email in (
        (ARTIST, "int_artist", "int_artist@test.local"),
        (REVIEWER, "int_reviewer", "int_reviewer@test.local"),
        (FINANCE, "int_finance", "int_finance@test.local"),
        (LISTENER, "int_listener", "int_listener@test.local"),
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

    def _member(user_id: int, role_code: str) -> None:
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
            [mid, ORG, user_id, now, ARTIST, now, now],
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
    _member(FINANCE, "billing_manager")

    conn.execute(
        """
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name,
             status, warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (1, ?, 'Integral Artist', NULL, 'integral artist', 'active', NULL, ?, ?, ?)
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

    # Good 60/40 + bad 90% contracts
    for aid, title in ((1, "Asset Good"), (2, "Asset Bad90")):
        conn.execute(
            """
            INSERT INTO app_catalog_asset
                (id, organization_id, title, status, warehouse_track_id,
                 artist_profile_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', NULL, 1, ?, ?, ?)
            """,
            [aid, ORG, title, ARTIST, now, now],
        )
        conn.execute(
            """
            INSERT INTO app_rights_contract
                (id, organization_id, asset_id, rights_type, status, exclusive,
                 valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
            """,
            [aid, ORG, aid, ARTIST, now, now],
        )
    conn.execute(
        """
        INSERT INTO app_rights_contract_party
            (id, contract_id, party_name, party_type, ownership_percentage,
             organization_id, artist_profile_id, created_at, updated_at)
        VALUES
            (1, 1, 'A', 'external', 60, NULL, NULL, ?, ?),
            (2, 1, 'B', 'external', 40, NULL, NULL, ?, ?),
            (3, 2, 'Solo', 'external', 90, NULL, NULL, ?, ?)
        """,
        [now, now, now, now, now, now],
    )

    media = LocalMediaStorageProvider(root=media_root)
    pub = CatalogPublishingUseCases(conn, media=media)
    yield conn, pub, media_root
    conn.close()
    schema_bootstrap._schema_ready = previous


def _ready_submission(uc, *, title="Integral Song", contract_id=1, catalog_asset_id=1):
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
    uc._conn.execute(
        """
        UPDATE app_release_submission_track
        SET catalog_asset_id = ?, rights_contract_id = ?
        WHERE id = ?
        """,
        [catalog_asset_id, contract_id, tr["id"]],
    )
    return draft["id"], tr["id"]


def _require_dim_track(conn) -> None:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'dim_track'"
    ).fetchone()
    if not row or int(row[0]) == 0:
        pytest.skip("soft-skip: warehouse dim_track missing")


def test_final_integral_chain(integral_db):
    """Publish → B2C Individual 4.99 checkout → royalties pool/settle/payout simulate."""
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
        get_subscription,
        list_personal_plans,
        simulate_payment,
        start_checkout,
    )
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases

    conn, pub, _ = integral_db
    _require_dim_track(conn)

    # --- Music path ---
    sid, _ = _ready_submission(pub, title="Final Integral")
    pub.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    pub.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)
    result = pub.publish(
        submission_id=sid,
        organization_id=ORG,
        actor_user_id=REVIEWER,
        idempotency_key="final-integral-pub-1",
    )
    assert result["submission"]["status"] == "published"
    wtid = result["warehouse_track_ids"][0]
    assert wtid >= DEMO_WAREHOUSE_TRACK_ID_MIN or wtid is not None
    src = get_audio_source_response(conn, wtid, force=True, async_resolve=False)
    assert src is not None
    assert src["provider"] == "local_published"
    assert src["status"] == "ok"

    # --- B2C personal path ---
    plans = list_personal_plans(conn)
    individual = next(p for p in plans if p["code"] == "premium_individual")
    amounts = {pr["billing_period"]: pr["amount"] for pr in individual["prices"]}
    assert amounts["monthly"] == 4.99
    ensure_free_subscription(conn, LISTENER)
    checkout = start_checkout(
        conn, LISTENER, plan_code="premium_individual", billing_period="monthly"
    )
    paid = simulate_payment(
        conn, LISTENER, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    assert paid["status"] == "succeeded"
    sub = get_subscription(conn, LISTENER)
    assert sub["plan_code"] == "premium_individual"
    assert sub["status"] == "active"

    # --- Royalty path (uses published warehouse_track_id + 60/40 contract) ---
    total = Decimal("100.0000")
    roy = RoyaltiesUseCases(conn)
    pool = roy.create_pool(
        actor_user_id=FINANCE,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
        idempotency_key="final-integral-pool-1",
        total_amount=total,
        label="final integral pool",
        is_demo=True,
    )
    roy.add_b2c_source(
        pool_id=pool["id"],
        actor_user_id=FINANCE,
        amount=total,
        currency="USD",
        source_payment_id="final-pay-demo-1",
        approve=True,
        organization_id=ORG,
    )
    pool = roy.approve_pool(pool_id=pool["id"], actor_user_id=FINANCE)
    assert pool["status"] == "approved"

    run = roy.calculate_pro_rata_settlement(
        pool_id=pool["id"],
        actor_user_id=FINANCE,
        idempotency_key="final-integral-settle-1",
        asset_scopes=[
            {"asset_id": 1, "warehouse_track_id": wtid, "rights_contract_id": 1},
        ],
        synthetic_event_counts={wtid: 100},
    )
    run = roy.calculate_contract_splits(settlement_run_id=run["id"], actor_user_id=FINANCE)
    party_nets = {p["party_id"]: p["net_amount"] for p in run["party_allocations"]}
    assert party_nets[1] == Decimal("60.0000")
    assert party_nets[2] == Decimal("40.0000")

    stmts = roy.generate_statements(settlement_run_id=run["id"], actor_user_id=FINANCE)
    assert len(stmts) == 2
    roy.submit_for_approval(settlement_run_id=run["id"], actor_user_id=FINANCE)
    run = roy.approve_settlement(settlement_run_id=run["id"], actor_user_id=FINANCE)
    assert run["status"] == "approved"

    batch = roy.create_payout_batch(
        settlement_run_id=run["id"],
        actor_user_id=FINANCE,
        idempotency_key="final-integral-payout-1",
    )
    batch = roy.simulate_payouts(
        batch_id=batch["id"], actor_user_id=FINANCE, scenario="succeed"
    )
    assert batch["status"] == "paid_simulated"
    assert all(i["destination_type"] == "demo_wallet" for i in batch["instructions"])


def test_contract_90_blocks_approve(integral_db):
    _, pub, _ = integral_db
    sid, _ = _ready_submission(pub, title="BadPct", contract_id=2, catalog_asset_id=2)
    pub.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    with pytest.raises(RightsGateError):
        pub.approve(submission_id=sid, organization_id=ORG, actor_user_id=REVIEWER)


def test_self_approve_blocked_when_demo_flag_off(integral_db):
    _, pub, _ = integral_db
    sid, _ = _ready_submission(pub, title="SelfBlock")
    pub.submit(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)
    with pytest.raises(SelfApproveError):
        pub.approve(submission_id=sid, organization_id=ORG, actor_user_id=ARTIST)


def test_listener_forbidden_crm_403(client: TestClient):
    """Listener (no CRM platform role) must get 403 on CRM."""
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import create_session, ensure_user_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables

    now = utc_now()
    with using_write_conn() as conn:
        ensure_user_tables(conn)
        ensure_crm_tables(conn)
        if not conn.execute("SELECT 1 FROM app_user WHERE id = ?", [LISTENER]).fetchone():
            conn.execute(
                """
                INSERT INTO app_user
                    (id, username, email, password_hash, role, plan, favorite_genre,
                     created_at, preferences_json, email_verified, auth_provider)
                VALUES (?, 'int_listener_api', 'int_listener_api@test.local', ?,
                        'user', 'Free', NULL, ?, '{}', TRUE, 'local')
                """,
                [LISTENER, hash_password("pass"), now],
            )
        token = create_session(conn, LISTENER)

    resp = client.get(
        "/api/v1/crm/prospects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
