"""Test J2: CRM use cases — Spec 017.

Covers:
- Agent creates prospect
- Manager approves discount
- Sent quotation is immutable
- Claim token is single-use
- No double conversion
- sales_agent is NOT org owner after Path B convert
"""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("crm_uc") / "test.duckdb"
    c = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now

    ensure_user_tables(c)
    ensure_organization_tables(c)
    ensure_platform_rbac_tables(c)
    ensure_crm_tables(c)
    ensure_commercial_contract_tables(c)

    now = utc_now()
    # Create agent user
    c.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [100, "agent_uc", "agent_uc@test.io", hash_password("x"), now],
    )
    # Create manager user
    c.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [101, "manager_uc", "manager_uc@test.io", hash_password("x"), now],
    )
    # Assign sales_agent role to user 100
    from app.packages.platform_rbac.infrastructure.repository import assign_role
    assign_role(c, user_id=100, role_code="sales_agent", assigned_by=None)
    assign_role(c, user_id=101, role_code="sales_manager", assigned_by=None)

    yield c
    c.close()
    schema_bootstrap._schema_ready = previous


# ── Prospect CRUD ─────────────────────────────────────────────────────────────

def test_create_prospect(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases
    p = ProspectUseCases(conn).create(
        actor_user_id=100,
        display_name="Acme Corp",
        company_name="Acme Ltd",
        email="acme@test.io",
    )
    assert p.id > 0
    assert p.status == "new"
    assert p.owner_user_id == 100


def test_prospect_initial_status_is_new(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases
    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="Beta Inc")
    assert p.status == "new"


def test_transition_prospect_status(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases
    uc = ProspectUseCases(conn)
    p = uc.create(actor_user_id=100, display_name="Gamma")
    updated = uc.transition_status(p.id, actor_user_id=100, new_status="contacted")
    assert updated.status == "contacted"


def test_list_prospects(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases
    items, total = ProspectUseCases(conn).list()
    assert total >= 1


# ── Opportunity stage history ─────────────────────────────────────────────────

def test_create_opportunity_records_stage_history(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases, OpportunityUseCases
    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="OppTest")
    o = OpportunityUseCases(conn).create(
        actor_user_id=100,
        prospect_id=p.id,
        name="First Deal",
        probability=20,
    )
    history = OpportunityUseCases(conn).stage_history(o.id)
    assert len(history) >= 1
    assert history[0].to_stage == "qualification"
    assert history[0].from_stage is None


def test_advance_opportunity_stage(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases, OpportunityUseCases
    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="OppStage")
    o = OpportunityUseCases(conn).create(actor_user_id=100, prospect_id=p.id, name="Stage Deal")
    updated = OpportunityUseCases(conn).advance_stage(o.id, actor_user_id=100, new_stage="proposal")
    assert updated.stage == "proposal"


def test_invalid_stage_transition_raises(conn):
    from app.packages.crm.application.use_cases import ProspectUseCases, OpportunityUseCases
    from app.packages.crm.domain.errors import ValidationError
    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="OppBadStage")
    o = OpportunityUseCases(conn).create(actor_user_id=100, prospect_id=p.id, name="Bad Stage")
    with pytest.raises(ValidationError):
        OpportunityUseCases(conn).advance_stage(o.id, actor_user_id=100, new_stage="closed_won")


# ── Quotation + discount approval ─────────────────────────────────────────────

def test_manager_approves_discount(conn):
    """Manager (user 101) approves a quotation version pending approval."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, QuotationUseCases, ApprovalUseCases,
    )
    p = ProspectUseCases(conn).create(actor_user_id=101, display_name="Discount Test")
    o = OpportunityUseCases(conn).create(actor_user_id=101, prospect_id=p.id, name="Discount Deal")
    q = QuotationUseCases(conn).create(actor_user_id=101, opportunity_id=o.id, currency="USD")
    version = QuotationUseCases(conn).create_version(q.id, actor_user_id=101)

    # Request approval for discount
    ar = QuotationUseCases(conn).request_discount_approval(
        version.id,
        actor_user_id=101,
        reason="Customer asked for 10% discount",
    )
    assert ar.status == "pending"

    # Manager approves
    approved = ApprovalUseCases(conn).approve(
        ar.id,
        actor_user_id=101,
        review_note="Approved for strategic reason",
    )
    assert approved.status == "approved"

    # Version should now be approved
    updated_version = QuotationUseCases(conn).get_version(version.id)
    assert updated_version.status == "approved"


def test_sent_quotation_version_is_immutable(conn):
    """Once a quotation version is sent, it cannot be modified."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, QuotationUseCases,
    )
    from app.packages.crm.domain.errors import ImmutableError
    p = ProspectUseCases(conn).create(actor_user_id=101, display_name="Immutable Test")
    o = OpportunityUseCases(conn).create(actor_user_id=101, prospect_id=p.id, name="Immutable Deal")
    q = QuotationUseCases(conn).create(actor_user_id=101, opportunity_id=o.id, currency="USD")
    version = QuotationUseCases(conn).create_version(q.id, actor_user_id=101)

    # Send it (no discount, so no approval needed if threshold=0 allows)
    # Use threshold=100 so no approval required for 0% discount
    sent_version = QuotationUseCases(conn).send_version(
        version.id, actor_user_id=101, discount_approval_threshold=100.0
    )
    assert sent_version.is_immutable is True
    assert sent_version.status == "sent"

    # Attempt to add item to immutable version
    from decimal import Decimal
    with pytest.raises(ImmutableError):
        QuotationUseCases(conn).add_item(
            version.id,
            actor_user_id=101,
            description="Extra item",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
        )


def test_discount_without_threshold_requires_approval(conn):
    """If no threshold configured, any discount > 0 requires approval before sending."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, QuotationUseCases,
    )
    from app.packages.crm.domain.errors import ApprovalRequiredError
    from decimal import Decimal

    p = ProspectUseCases(conn).create(actor_user_id=101, display_name="NoThreshold Test")
    o = OpportunityUseCases(conn).create(actor_user_id=101, prospect_id=p.id, name="NoThreshold Deal")
    q = QuotationUseCases(conn).create(actor_user_id=101, opportunity_id=o.id, currency="USD")
    version = QuotationUseCases(conn).create_version(q.id, actor_user_id=101)
    QuotationUseCases(conn).add_item(
        version.id,
        actor_user_id=101,
        description="Item",
        quantity=Decimal("1"),
        unit_price=Decimal("100"),
        discount_pct=Decimal("5"),
    )

    with pytest.raises(ApprovalRequiredError):
        QuotationUseCases(conn).send_version(
            version.id,
            actor_user_id=101,
            discount_approval_threshold=None,  # None = any discount requires approval
        )


# ── Conversion — single-use token ─────────────────────────────────────────────

def test_claim_token_is_single_use(conn):
    """Once a token is consumed, a second claim with the same token fails."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, ConversionUseCases,
    )
    from app.packages.crm.domain.errors import TokenAlreadyUsedError, PersistenceError

    # Create a signatory user
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now
    now = utc_now()
    conn.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [200, "signatory_test", "signatory@test.io", hash_password("x"), now],
    )

    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="Token Test")
    o = OpportunityUseCases(conn).create(actor_user_id=100, prospect_id=p.id, name="Token Deal")

    conv, raw_token = ConversionUseCases(conn).prepare(
        actor_user_id=100,
        opportunity_id=o.id,
        mode="create_org",
        idempotency_key=f"token-test-{o.id}",
    )
    assert raw_token is not None
    assert conv.status == "awaiting_customer_claim"

    # First claim - should succeed (creates org)
    claimed = ConversionUseCases(conn).claim(
        conv.id,
        raw_token=raw_token,
        actor_user_id=200,
        org_display_name="Acme Organization",
        org_slug=f"acme-org-{o.id}",
    )
    assert claimed.status == "completed"
    assert claimed.organization_id is not None

    # Second claim - should fail
    with pytest.raises((TokenAlreadyUsedError, PersistenceError)):
        ConversionUseCases(conn).claim(
            conv.id,
            raw_token=raw_token,
            actor_user_id=200,
            org_display_name="Acme Organization 2",
            org_slug=f"acme-org-{o.id}-2",
        )


def test_no_double_conversion(conn):
    """Cannot create a second completed conversion for the same opportunity."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, ConversionUseCases,
    )
    from app.packages.crm.domain.errors import ConversionConflict

    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now
    now = utc_now()
    conn.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [201, "signatory2", "signatory2@test.io", hash_password("x"), now],
    )

    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="NoDblConv")
    o = OpportunityUseCases(conn).create(actor_user_id=100, prospect_id=p.id, name="NoDbl Deal")

    conv, raw_token = ConversionUseCases(conn).prepare(
        actor_user_id=100,
        opportunity_id=o.id,
        mode="create_org",
        idempotency_key=f"nodbl-{o.id}",
    )
    # Claim it
    ConversionUseCases(conn).claim(
        conv.id,
        raw_token=raw_token,
        actor_user_id=201,
        org_display_name="NoDbl Org",
        org_slug=f"nodbl-org-{o.id}",
    )

    # Now try to prepare another conversion for the same opportunity
    with pytest.raises(ConversionConflict):
        ConversionUseCases(conn).prepare(
            actor_user_id=100,
            opportunity_id=o.id,
            mode="create_org",
        )


def test_sales_agent_is_not_org_owner_after_conversion(conn):
    """After Path B conversion, the signatory user owns the org — not the sales agent."""
    from app.packages.crm.application.use_cases import (
        ProspectUseCases, OpportunityUseCases, ConversionUseCases,
    )
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now
    now = utc_now()
    conn.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [202, "signatory3", "signatory3@test.io", hash_password("x"), now],
    )

    p = ProspectUseCases(conn).create(actor_user_id=100, display_name="AgentNotOwner")
    o = OpportunityUseCases(conn).create(actor_user_id=100, prospect_id=p.id, name="AgentNotOwner Deal")

    conv, raw_token = ConversionUseCases(conn).prepare(
        actor_user_id=100,
        opportunity_id=o.id,
        mode="create_org",
        idempotency_key=f"ano-{o.id}",
    )
    # Signatory (202) claims
    claimed = ConversionUseCases(conn).claim(
        conv.id,
        raw_token=raw_token,
        actor_user_id=202,
        org_display_name="AgentNotOwner Org",
        org_slug=f"agentnotowner-{o.id}",
    )
    org_id = claimed.organization_id
    assert org_id is not None

    # Signatory (202) should be owner
    signatory_is_owner = conn.execute(
        """
        SELECT 1
        FROM app_organization_member m
        JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        JOIN app_business_role br ON br.id = mr.role_id AND br.code = 'owner'
        WHERE m.organization_id = ? AND m.user_id = ?
        LIMIT 1
        """,
        [org_id, 202],
    ).fetchone()
    assert signatory_is_owner is not None, "Signatory should be org owner"

    # Sales agent (100) should NOT be a member or owner
    agent_is_owner = conn.execute(
        """
        SELECT 1
        FROM app_organization_member m
        JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        JOIN app_business_role br ON br.id = mr.role_id AND br.code = 'owner'
        WHERE m.organization_id = ? AND m.user_id = ?
        LIMIT 1
        """,
        [org_id, 100],
    ).fetchone()
    assert agent_is_owner is None, "Sales agent must NOT be org owner after Path B"
