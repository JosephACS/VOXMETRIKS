"""Test R2: Platform ops use cases — Spec 027."""

from __future__ import annotations

import duckdb
import pytest

from app.packages.platform_ops.application.use_cases import (
    FeatureFlagUseCases,
    JobUseCases,
    NotificationUseCases,
    ProviderConfigUseCases,
    WebhookUseCases,
    redact_secret,
)
from app.packages.platform_ops.domain.errors import IdempotencyError, ValidationError


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("platform_ops_uc") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_ops_tables(conn)

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_notification_labeled_mock(db_conn):
    n, d = NotificationUseCases(db_conn).send(
        actor_user_id=1, recipient="user@test", subject="Test", body="Hello",
    )
    assert n.status == "sent"
    assert d.labeled_mock is True


def test_webhook_idempotency(db_conn):
    WebhookUseCases(db_conn).receive(
        source="billing", event_type="payment", idempotency_key="idem-1", payload={"a": 1},
    )
    with pytest.raises(IdempotencyError):
        WebhookUseCases(db_conn).receive(
            source="billing", event_type="payment", idempotency_key="idem-1", payload={"a": 2},
        )


def test_job_retry_and_dead_letter(db_conn):
    job = JobUseCases(db_conn).register(
        actor_user_id=1, job_code="test_job", display_name="Test", max_retries=2,
    )
    ex1 = JobUseCases(db_conn).execute(job.id, actor_user_id=1, simulate_failure=True)
    assert ex1.status == "failed"
    ex2 = JobUseCases(db_conn).execute(job.id, actor_user_id=1, simulate_failure=True)
    assert ex2.status == "dead_letter"
    assert ex2.dead_letter is True


def test_secret_ref_validation(db_conn):
    with pytest.raises(ValidationError):
        ProviderConfigUseCases(db_conn).register(
            actor_user_id=1, provider_code="bad", display_name="Bad", secret_ref="raw-secret",
        )


def test_redact_secret():
    assert redact_secret("secret://billing/key123") == "se****23"
    assert redact_secret(None) is None


def test_feature_flag_upsert(db_conn):
    f = FeatureFlagUseCases(db_conn).upsert(
        actor_user_id=1, flag_key="test_flag", description="Test", enabled=True,
    )
    assert f.enabled is True
    f2 = FeatureFlagUseCases(db_conn).upsert(
        actor_user_id=1, flag_key="test_flag", description="Updated", enabled=False,
    )
    assert f2.id == f.id
    assert f2.enabled is False
