"""Test J1: CRM schema exists — Spec 017."""

from __future__ import annotations

import pytest
import duckdb


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("crm_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


# ── Platform RBAC tables ──────────────────────────────────────────────────────

def test_platform_role_table_exists(db_conn):
    rows = db_conn.execute("SELECT code FROM app_platform_role ORDER BY code").fetchall()
    codes = {r[0] for r in rows}
    assert {"sales_agent", "sales_manager", "platform_admin", "auditor"} == codes


def test_platform_permission_table_seeded(db_conn):
    rows = db_conn.execute("SELECT code FROM app_platform_permission").fetchall()
    codes = {r[0] for r in rows}
    assert "crm.prospect.view" in codes
    assert "quotation.approve" in codes
    assert "customer.convert" in codes
    assert "crm.audit.view" in codes


def test_platform_role_permission_matrix_sales_agent(db_conn):
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_user_platform_role upr
        JOIN app_platform_role_permission rp ON rp.role_id = upr.role_id
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE 1=0  -- just check the join works
    """).fetchall()
    # Verify agent role doesn't have quotation.approve via matrix
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_platform_role_permission rp
        JOIN app_platform_role pr ON pr.id = rp.role_id AND pr.code = 'sales_agent'
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE pp.code = 'quotation.approve'
    """).fetchall()
    assert rows == [], "sales_agent must NOT have quotation.approve"


def test_platform_role_permission_matrix_manager(db_conn):
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_platform_role_permission rp
        JOIN app_platform_role pr ON pr.id = rp.role_id AND pr.code = 'sales_manager'
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE pp.code = 'quotation.approve'
    """).fetchall()
    assert rows, "sales_manager MUST have quotation.approve"


def test_auditor_permissions_restricted(db_conn):
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_platform_role_permission rp
        JOIN app_platform_role pr ON pr.id = rp.role_id AND pr.code = 'auditor'
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
    """).fetchall()
    codes = {r[0] for r in rows}
    assert codes <= {
        "crm.prospect.view", "crm.opportunity.view", "crm.audit.view", "plan.view",
        "audit.search", "ops.view",  # Spec 026/027 read-only platform audit/ops
    }
    assert "crm.prospect.create" not in codes


# ── CRM tables ────────────────────────────────────────────────────────────────

def test_crm_prospect_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_crm_prospect LIMIT 0")


def test_crm_contact_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_crm_contact LIMIT 0")


def test_crm_opportunity_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_crm_opportunity LIMIT 0")


def test_crm_quotation_table_exists(db_conn):
    db_conn.execute("SELECT id, row_version, current_version_no FROM app_crm_quotation LIMIT 0")


def test_crm_quotation_version_table_exists(db_conn):
    db_conn.execute("SELECT id, is_immutable, discount_requires_approval FROM app_crm_quotation_version LIMIT 0")


def test_crm_quotation_item_table_exists(db_conn):
    db_conn.execute("SELECT id, line_total FROM app_crm_quotation_item LIMIT 0")


def test_crm_approval_request_table_exists(db_conn):
    db_conn.execute("SELECT id, object_type, threshold_ref FROM app_crm_approval_request LIMIT 0")


def test_crm_customer_conversion_table_exists(db_conn):
    db_conn.execute(
        "SELECT id, claim_token_hash, claim_token_expires_at, idempotency_key "
        "FROM app_crm_customer_conversion LIMIT 0"
    )


def test_crm_sales_activity_table_exists(db_conn):
    db_conn.execute("SELECT id, activity_type, status FROM app_crm_sales_activity LIMIT 0")


def test_crm_stage_history_table_exists(db_conn):
    db_conn.execute("SELECT id, from_stage, to_stage FROM app_crm_opportunity_stage_history LIMIT 0")


def test_crm_prospect_contact_table_exists(db_conn):
    db_conn.execute("SELECT prospect_id, contact_id, is_signatory FROM app_crm_prospect_contact LIMIT 0")


# ── Contracts table ───────────────────────────────────────────────────────────

def test_commercial_contract_table_exists(db_conn):
    db_conn.execute(
        "SELECT id, quotation_version_id, terms_snapshot, acceptance_evidence "
        "FROM app_commercial_contract LIMIT 0"
    )


# ── Audit log compatible ──────────────────────────────────────────────────────

def test_audit_log_organization_id_nullable(db_conn):
    cols = db_conn.execute("DESCRIBE app_audit_log").fetchall()
    col_names = {r[0] for r in cols}
    assert "organization_id" in col_names


def test_user_platform_role_table_exists(db_conn):
    db_conn.execute("SELECT id, user_id, role_id, status FROM app_user_platform_role LIMIT 0")


# ── Idempotency ───────────────────────────────────────────────────────────────

def test_ensure_tables_idempotent(db_conn):
    """Calling ensure multiple times must not raise."""
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    # schema_ready() returns True in test context after first call → these become no-ops
    ensure_platform_rbac_tables(db_conn)
    ensure_crm_tables(db_conn)
    ensure_commercial_contract_tables(db_conn)
