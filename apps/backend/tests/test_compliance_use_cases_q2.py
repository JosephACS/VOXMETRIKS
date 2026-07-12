"""Test Q2: Compliance use cases — Spec 026."""

from __future__ import annotations

import duckdb
import pytest

from app.packages.compliance.application.use_cases import (
    ConsentDefinitionUseCases,
    ConsentRecordUseCases,
    DataRequestUseCases,
    LegalHoldUseCases,
    RetentionPolicyUseCases,
    TermsAcceptanceUseCases,
    TermsVersionUseCases,
)
from app.packages.compliance.domain.errors import DeletionBlockedError, ValidationError


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("compliance_uc") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.compliance.infrastructure.schema import ensure_compliance_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_compliance_tables(conn)

    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, slug, organization_type, country_code, timezone,
             default_currency, status, created_by, created_at, updated_at)
        VALUES (80, 'Compliance UC Org', 'compliance-uc', 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
        """,
        [now, now],
    )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_terms_publish_and_accept(db_conn):
    from app.core.time_util import utc_now

    tv = TermsVersionUseCases(db_conn).create(
        actor_user_id=1,
        version_code="v1.0",
        title="Terms",
        content_summary="Summary",
        effective_at=utc_now(),
    )
    published = TermsVersionUseCases(db_conn).publish(tv.id, actor_user_id=1)
    assert published.status == "published"
    acc = TermsAcceptanceUseCases(db_conn).accept(user_id=2, terms_version_id=tv.id, organization_id=80)
    assert acc.user_id == 2


def test_consent_grant_and_withdraw(db_conn):
    defn = ConsentDefinitionUseCases(db_conn).create(
        actor_user_id=1, code="marketing", title="Marketing", description="Opt-in",
        organization_id=80,
    )
    rec = ConsentRecordUseCases(db_conn).grant(
        user_id=2, consent_definition_id=defn.id, organization_id=80,
    )
    assert rec.status == "granted"
    withdrawn = ConsentRecordUseCases(db_conn).withdraw(rec.id, user_id=2, organization_id=80)
    assert withdrawn.status == "withdrawn"


def test_deletion_blocked_by_legal_hold_and_retention(db_conn):
    LegalHoldUseCases(db_conn).place(
        actor_user_id=1, organization_id=80, subject_type="user", subject_id="2",
        reason="Litigation hold",
    )
    RetentionPolicyUseCases(db_conn).create(
        actor_user_id=1, organization_id=80, data_category="user_data", retention_days=365,
    )
    dr = DataRequestUseCases(db_conn).submit(
        requester_user_id=2, organization_id=80, request_type="deletion",
    )
    with pytest.raises(DeletionBlockedError) as exc:
        DataRequestUseCases(db_conn).process_deletion(
            dr.id, 80, actor_user_id=1,
        )
    assert "legal_hold" in exc.value.blockers or "retention_policy" in exc.value.blockers


def test_sensitive_access_requires_reason(db_conn):
    from app.packages.compliance.application.use_cases import SensitiveAccessUseCases

    with pytest.raises(ValidationError):
        SensitiveAccessUseCases(db_conn).record(
            accessor_user_id=1, resource_type="profile", resource_id="2", reason="  ",
            organization_id=80,
        )
