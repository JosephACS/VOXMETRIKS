"""Spec 030 — Royalties golden path + negatives (Decimal money, no real payouts)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import duckdb
import pytest
from fastapi.testclient import TestClient


ACTOR = 9101
ORG = 9300
VIEWER = 9102


@pytest.fixture()
def royalty_db(tmp_path):
    from app.core import schema_bootstrap
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.royalties.infrastructure.schema import ensure_royalty_tables

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "royalties_s030.duckdb"))

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_royalty_tables(conn)

    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at)
        VALUES (?, 'Royalty Org', 'Royalty Org LLC', 'royalty-org-s030', 'label', 'US',
                'UTC', 'USD', 'active', ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    for uid, uname, email in (
        (ACTOR, "royalty_actor", "royalty_actor@test.local"),
        (VIEWER, "royalty_viewer", "royalty_viewer@test.local"),
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
        mid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, joined_at, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [mid, ORG, user_id, now, ACTOR, now, now],
        )
        mrid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            [mrid, mid, role_ids[role_code], ACTOR, now],
        )

    _member(ACTOR, "billing_manager")
    _member(VIEWER, "viewer")

    conn.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id,
             artist_profile_id, created_by, created_at, updated_at)
        VALUES (1, ?, 'Track One', 'active', 101, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract
            (id, organization_id, asset_id, rights_type, status, exclusive,
             valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
        VALUES (1, ?, 1, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_rights_contract_party
            (id, contract_id, party_name, party_type, ownership_percentage,
             organization_id, artist_profile_id, created_at, updated_at)
        VALUES
            (1, 1, 'Artist A', 'external', 60, NULL, NULL, ?, ?),
            (2, 1, 'Label B', 'external', 40, NULL, NULL, ?, ?)
        """,
        [now, now, now, now],
    )

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


def _happy_path(conn, *, total: Decimal = Decimal("100.0000")):
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases

    uc = RoyaltiesUseCases(conn)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        idempotency_key="gp-pool-1",
        total_amount=total,
        label="golden path pool",
        is_demo=True,
    )
    uc.add_b2c_source(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        amount=total,
        currency="USD",
        source_payment_id="pay-demo-1",
        approve=True,
        organization_id=ORG,
    )
    pool = uc.approve_pool(pool_id=pool["id"], actor_user_id=ACTOR)
    assert pool["status"] == "approved"
    assert isinstance(pool["total_amount"], Decimal)

    run = uc.calculate_pro_rata_settlement(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        idempotency_key="gp-settle-1",
        asset_scopes=[
            {"asset_id": 1, "warehouse_track_id": 101, "rights_contract_id": 1},
        ],
        synthetic_event_counts={101: 100},
    )
    assert run["status"] == "calculated"
    run = uc.calculate_contract_splits(settlement_run_id=run["id"], actor_user_id=ACTOR)
    assert run["status"] == "calculated"
    party_nets = {p["party_id"]: p["net_amount"] for p in run["party_allocations"]}
    assert party_nets[1] == Decimal("60.0000")
    assert party_nets[2] == Decimal("40.0000")
    assert sum(party_nets.values(), Decimal("0")) == total

    stmts = uc.generate_statements(settlement_run_id=run["id"], actor_user_id=ACTOR)
    assert len(stmts) == 2
    assert all(isinstance(s["net_amount"], Decimal) for s in stmts)

    uc.submit_for_approval(settlement_run_id=run["id"], actor_user_id=ACTOR)
    run = uc.approve_settlement(settlement_run_id=run["id"], actor_user_id=ACTOR)
    assert run["status"] == "approved"

    batch = uc.create_payout_batch(
        settlement_run_id=run["id"],
        actor_user_id=ACTOR,
        idempotency_key="gp-payout-1",
    )
    batch = uc.simulate_payouts(batch_id=batch["id"], actor_user_id=ACTOR, scenario="succeed")
    assert batch["status"] == "paid_simulated"
    assert all(i["destination_type"] == "demo_wallet" for i in batch["instructions"])
    return uc, pool, run, batch


def test_golden_path_happy(royalty_db):
    from app.packages.royalties.domain.errors import SettlementFinalizedError

    uc, pool, run, batch = _happy_path(royalty_db)
    metrics = uc.metrics_dashboard(organization_id=ORG)
    assert metrics["simulated_only"] is True
    assert "not equal" in metrics["income_note"].lower()
    assert isinstance(metrics["distributable_pool_approved"], Decimal)

    again = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        idempotency_key="gp-pool-1",
        total_amount=Decimal("100.0000"),
    )
    assert again["id"] == pool["id"]

    dup = uc.create_payout_batch(
        settlement_run_id=run["id"],
        actor_user_id=ACTOR,
        idempotency_key="gp-payout-1",
    )
    assert dup["id"] == batch["id"]

    uc.finalize_settlement(settlement_run_id=run["id"], actor_user_id=ACTOR)
    with pytest.raises(SettlementFinalizedError):
        uc.apply_adjustment(
            settlement_run_id=run["id"],
            actor_user_id=ACTOR,
            amount=Decimal("1.0000"),
            reason="should fail",
        )


def test_ownership_sum_90_blocks(royalty_db):
    from app.core.time_util import utc_now
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases
    from app.packages.royalties.domain.errors import OwnershipSumError

    now = utc_now()
    royalty_db.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id,
             artist_profile_id, created_by, created_at, updated_at)
        VALUES (2, ?, 'Bad Split', 'active', 202, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    royalty_db.execute(
        """
        INSERT INTO app_rights_contract
            (id, organization_id, asset_id, rights_type, status, exclusive,
             valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
        VALUES (2, ?, 2, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    royalty_db.execute(
        """
        INSERT INTO app_rights_contract_party
            (id, contract_id, party_name, party_type, ownership_percentage,
             organization_id, artist_profile_id, created_at, updated_at)
        VALUES
            (10, 2, 'A', 'external', 50, NULL, NULL, ?, ?),
            (11, 2, 'B', 'external', 40, NULL, NULL, ?, ?)
        """,
        [now, now, now, now],
    )

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 2, 1),
        period_end=date(2026, 2, 28),
        idempotency_key="bad-own-pool",
        total_amount=Decimal("10.0000"),
    )
    uc.approve_pool(pool_id=pool["id"], actor_user_id=ACTOR)
    run = uc.calculate_pro_rata_settlement(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        idempotency_key="bad-own-settle",
        asset_scopes=[
            {"asset_id": 2, "warehouse_track_id": 202, "rights_contract_id": 2},
        ],
        synthetic_event_counts={202: 10},
    )
    with pytest.raises(OwnershipSumError):
        uc.calculate_contract_splits(settlement_run_id=run["id"], actor_user_id=ACTOR)
    assert uc.get_settlement(run["id"])["status"] == "blocked"


def test_wrong_currency_rejected(royalty_db):
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases
    from app.packages.royalties.domain.errors import CurrencyMismatchError

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        idempotency_key="fx-pool",
        total_amount=Decimal("5.0000"),
    )
    with pytest.raises(CurrencyMismatchError):
        uc.add_b2c_source(
            pool_id=pool["id"],
            actor_user_id=ACTOR,
            amount=Decimal("5.0000"),
            currency="EUR",
            approve=True,
        )


def test_b2b_not_automatic(royalty_db):
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases
    from app.packages.royalties.domain.errors import B2BRequiresManualAttributionError

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        idempotency_key="b2b-pool",
        total_amount=Decimal("5.0000"),
    )
    with pytest.raises(B2BRequiresManualAttributionError):
        uc.add_b2c_source(
            pool_id=pool["id"],
            actor_user_id=ACTOR,
            amount=Decimal("5.0000"),
            currency="USD",
            source_kind="B2B_MANUAL",
        )
    src = uc.add_manual_b2b_source(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        amount=Decimal("5.0000"),
        currency="USD",
        reason="Audited B2B MANUAL_ATTRIBUTION",
        source_invoice_id="inv-99",
    )
    assert src["source_kind"] == "B2B_MANUAL"
    assert src["status"] == "approved"


def test_unapproved_settlement_cannot_payout(royalty_db):
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases
    from app.packages.royalties.domain.errors import SettlementNotApprovedError

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 31),
        idempotency_key="early-pay-pool",
        total_amount=Decimal("20.0000"),
    )
    uc.approve_pool(pool_id=pool["id"], actor_user_id=ACTOR)
    run = uc.calculate_pro_rata_settlement(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        idempotency_key="early-pay-settle",
        asset_scopes=[
            {"asset_id": 1, "warehouse_track_id": 101, "rights_contract_id": 1},
        ],
        synthetic_event_counts={101: 20},
    )
    uc.calculate_contract_splits(settlement_run_id=run["id"], actor_user_id=ACTOR)
    uc.generate_statements(settlement_run_id=run["id"], actor_user_id=ACTOR)
    with pytest.raises(SettlementNotApprovedError):
        uc.create_payout_batch(
            settlement_run_id=run["id"],
            actor_user_id=ACTOR,
            idempotency_key="early-pay-batch",
        )


def test_settle_requires_approved_pool(royalty_db):
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases
    from app.packages.royalties.domain.errors import PoolNotApprovedError

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        idempotency_key="draft-settle-pool",
        total_amount=Decimal("10.0000"),
    )
    with pytest.raises(PoolNotApprovedError):
        uc.calculate_pro_rata_settlement(
            pool_id=pool["id"],
            actor_user_id=ACTOR,
            idempotency_key="draft-settle",
            synthetic_event_counts={101: 1},
            asset_scopes=[
                {"asset_id": 1, "warehouse_track_id": 101, "rights_contract_id": 1},
            ],
        )


def test_remainder_sums_to_total(royalty_db):
    from app.core.time_util import utc_now
    from app.packages.royalties.application.use_cases import RoyaltiesUseCases

    now = utc_now()
    royalty_db.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id,
             artist_profile_id, created_by, created_at, updated_at)
        VALUES (3, ?, 'Tri Split', 'active', 303, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    royalty_db.execute(
        """
        INSERT INTO app_rights_contract
            (id, organization_id, asset_id, rights_type, status, exclusive,
             valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
        VALUES (3, ?, 3, 'master', 'active', FALSE, DATE '2020-01-01', NULL, NULL, ?, ?, ?)
        """,
        [ORG, ACTOR, now, now],
    )
    for pid, name, pct in (
        (20, "P1", Decimal("33.3333")),
        (21, "P2", Decimal("33.3333")),
        (22, "P3", Decimal("33.3334")),
    ):
        royalty_db.execute(
            """
            INSERT INTO app_rights_contract_party
                (id, contract_id, party_name, party_type, ownership_percentage,
                 organization_id, artist_profile_id, created_at, updated_at)
            VALUES (?, 3, ?, 'external', ?, NULL, NULL, ?, ?)
            """,
            [pid, name, pct, now, now],
        )

    uc = RoyaltiesUseCases(royalty_db)
    pool = uc.create_pool(
        actor_user_id=ACTOR,
        organization_id=ORG,
        currency="USD",
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
        idempotency_key="rem-pool",
        total_amount=Decimal("10.0000"),
    )
    uc.approve_pool(pool_id=pool["id"], actor_user_id=ACTOR)
    run = uc.calculate_pro_rata_settlement(
        pool_id=pool["id"],
        actor_user_id=ACTOR,
        idempotency_key="rem-settle",
        asset_scopes=[
            {"asset_id": 3, "warehouse_track_id": 303, "rights_contract_id": 3},
        ],
        synthetic_event_counts={303: 10},
    )
    run = uc.calculate_contract_splits(settlement_run_id=run["id"], actor_user_id=ACTOR)
    nets = [p["net_amount"] for p in run["party_allocations"]]
    assert sum(nets, Decimal("0")) == Decimal("10.0000")
    assert all(isinstance(n, Decimal) for n in nets)


def test_api_no_permission(client: TestClient):
    """Authenticated org member without royalty.view gets 403."""
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import create_session, ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.royalties.infrastructure.schema import ensure_royalty_tables

    now = utc_now()
    with using_write_conn() as conn:
        ensure_user_tables(conn)
        ensure_organization_tables(conn)
        ensure_royalty_tables(conn)

        if not conn.execute("SELECT 1 FROM app_organization WHERE id = ?", [ORG]).fetchone():
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (?, 'Royalty Org API', 'Royalty Org API', 'royalty-org-s030-api', 'label',
                        'US', 'UTC', 'USD', 'active', 1, ?, ?)
                """,
                [ORG, now, now],
            )
        if not conn.execute("SELECT 1 FROM app_user WHERE id = ?", [VIEWER]).fetchone():
            conn.execute(
                """
                INSERT INTO app_user
                    (id, username, email, password_hash, role, plan, favorite_genre,
                     created_at, preferences_json, email_verified, auth_provider)
                VALUES (?, 'royalty_viewer_api', 'royalty_viewer_api@test.local', ?,
                        'user', 'Free', NULL, ?, '{}', TRUE, 'local')
                """,
                [VIEWER, hash_password("pass"), now],
            )
        role_ids = {
            r[0]: int(r[1])
            for r in conn.execute("SELECT code, id FROM app_business_role").fetchall()
        }
        if not conn.execute(
            "SELECT 1 FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
            [ORG, VIEWER],
        ).fetchone():
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
                [mid, ORG, VIEWER, now, VIEWER, now, now],
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
                [mrid, mid, role_ids["viewer"], VIEWER, now],
            )
        token = create_session(conn, VIEWER)

    resp = client.get(
        "/api/v1/royalties/pools",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": str(ORG),
        },
    )
    assert resp.status_code == 403
    body = resp.json()
    nested = body.get("details") or body.get("detail") or body
    if isinstance(nested, dict):
        assert nested.get("code") == "permission_denied"
    else:
        assert "permission" in str(body).lower()