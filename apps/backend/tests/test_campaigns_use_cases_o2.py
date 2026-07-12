"""Test O2: Campaigns use cases — Spec 022."""

from __future__ import annotations

from datetime import date

import duckdb
import pytest

from app.packages.campaigns.application.use_cases import (
    AttributionDefinitionUseCases,
    AttributableRevenueUseCases,
    CampaignApprovalUseCases,
    CampaignBudgetUseCases,
    CampaignExpenseUseCases,
    CampaignResultUseCases,
    CampaignRoiUseCases,
    CampaignTargetUseCases,
    CampaignUseCases,
)
from app.packages.campaigns.domain.errors import (
    BudgetExceededError,
    InvalidTransitionError,
    NotFoundError,
    SeparationOfDutiesError,
)


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("campaigns_uc") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_campaign_tables(conn)

    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, slug, organization_type, country_code, timezone,
             default_currency, status, created_by, created_at, updated_at)
        VALUES (50, 'Campaigns UC Org', 'campaigns-uc', 'label', 'US', 'UTC', 'USD',
                'active', 1, ?, ?)
        """,
        [now, now],
    )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


ORG_ID = 50
ACTOR = 1
APPROVER = 2
PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 3, 31)


@pytest.fixture
def campaign_id(db_conn) -> int:
    c = CampaignUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG_ID, name="Test Campaign",
        start_date=PERIOD_START, end_date=PERIOD_END,
    )
    return c.id


def test_create_and_get_campaign(db_conn, campaign_id):
    c = CampaignUseCases(db_conn).get(campaign_id, ORG_ID)
    assert c.name == "Test Campaign"
    assert c.status == "draft"


def test_cross_org_not_found(db_conn, campaign_id):
    with pytest.raises(NotFoundError):
        CampaignUseCases(db_conn).get(campaign_id, 9999)


def test_submit_and_approve_campaign(db_conn, campaign_id):
    approval = CampaignApprovalUseCases(db_conn).submit(
        campaign_id, ORG_ID, approval_type="launch", actor_user_id=ACTOR,
    )
    decided = CampaignApprovalUseCases(db_conn).decide(
        approval.id, ORG_ID, approved=True, actor_user_id=APPROVER,
    )
    assert decided.status == "approved"
    c = CampaignUseCases(db_conn).get(campaign_id, ORG_ID)
    assert c.status == "approved"


def test_separation_of_duties(db_conn, campaign_id):
    approval = CampaignApprovalUseCases(db_conn).submit(
        campaign_id, ORG_ID, approval_type="budget_override", actor_user_id=ACTOR,
    )
    with pytest.raises(SeparationOfDutiesError):
        CampaignApprovalUseCases(db_conn).decide(
            approval.id, ORG_ID, approved=True, actor_user_id=ACTOR,
        )


def test_budget_and_expense_block(db_conn, campaign_id):
    CampaignBudgetUseCases(db_conn).set(
        campaign_id, ORG_ID, amount=1000.0, currency="USD",
    )
    with pytest.raises(BudgetExceededError):
        CampaignExpenseUseCases(db_conn).add(
            campaign_id, ORG_ID, amount=1500.0, currency="USD",
            category="ads", expense_date=PERIOD_START, actor_user_id=ACTOR,
        )


def test_expense_with_override(db_conn, campaign_id):
    CampaignBudgetUseCases(db_conn).set(
        campaign_id, ORG_ID, amount=1000.0, currency="USD",
    )
    override = CampaignApprovalUseCases(db_conn).submit(
        campaign_id, ORG_ID, approval_type="expense_override", actor_user_id=ACTOR,
    )
    CampaignApprovalUseCases(db_conn).decide(
        override.id, ORG_ID, approved=True, actor_user_id=APPROVER,
    )
    expense = CampaignExpenseUseCases(db_conn).add(
        campaign_id, ORG_ID, amount=1500.0, currency="USD",
        category="ads", expense_date=PERIOD_START, actor_user_id=ACTOR,
        override_id=override.id,
    )
    assert expense.amount == 1500.0


def test_roi_unavailable_without_data(db_conn, campaign_id):
    snapshot = CampaignRoiUseCases(db_conn).compute_snapshot(campaign_id, ORG_ID, actor_user_id=ACTOR)
    assert snapshot.status == "unavailable"
    assert snapshot.roi_value is None
    assert snapshot.unavailable_reason is not None


def test_roi_available_with_full_data(db_conn, campaign_id):
    CampaignBudgetUseCases(db_conn).set(campaign_id, ORG_ID, amount=5000.0, currency="USD")
    CampaignExpenseUseCases(db_conn).add(
        campaign_id, ORG_ID, amount=2000.0, currency="USD",
        category="media", expense_date=PERIOD_START, actor_user_id=ACTOR,
    )
    attr = AttributionDefinitionUseCases(db_conn).create(
        campaign_id, ORG_ID, model_code="last_touch", confidence=0.85,
        responsible="finance@org.com",
    )
    AttributionDefinitionUseCases(db_conn).approve(attr.id, ORG_ID, actor_user_id=APPROVER)
    rev = AttributableRevenueUseCases(db_conn).record(
        campaign_id, ORG_ID, attribution_definition_id=attr.id,
        amount=8000.0, currency="USD", period_start=PERIOD_START, period_end=PERIOD_END,
    )
    AttributableRevenueUseCases(db_conn).approve(rev.id, ORG_ID, actor_user_id=APPROVER)
    CampaignTargetUseCases(db_conn).set(
        campaign_id, ORG_ID, metric_code="streams", target_value=10000.0,
    )
    CampaignResultUseCases(db_conn).record(
        campaign_id, ORG_ID, metric_code="streams", value=12000.0,
        is_monetary=False, source_label="warehouse:fact_streaming",
    )

    snapshot = CampaignRoiUseCases(db_conn).compute_snapshot(campaign_id, ORG_ID, actor_user_id=ACTOR)
    assert snapshot.status == "available"
    assert snapshot.roi_value == pytest.approx(3.0)
    assert snapshot.budget_utilization == pytest.approx(0.4)
    assert snapshot.goal_attainment == pytest.approx(1.2)
    assert snapshot.engagement_lift == 12000.0


def test_streams_not_treated_as_money(db_conn, campaign_id):
    CampaignResultUseCases(db_conn).record(
        campaign_id, ORG_ID, metric_code="streams", value=50000.0, is_monetary=False,
    )
    CampaignBudgetUseCases(db_conn).set(campaign_id, ORG_ID, amount=1000.0, currency="USD")
    CampaignExpenseUseCases(db_conn).add(
        campaign_id, ORG_ID, amount=500.0, currency="USD",
        category="ads", expense_date=PERIOD_START, actor_user_id=ACTOR,
    )
    snapshot = CampaignRoiUseCases(db_conn).compute_snapshot(campaign_id, ORG_ID)
    assert snapshot.engagement_lift == 50000.0
    assert snapshot.status == "unavailable"


def test_invalid_transition(db_conn, campaign_id):
    with pytest.raises(InvalidTransitionError):
        CampaignUseCases(db_conn).activate(campaign_id, ORG_ID, actor_user_id=ACTOR)
