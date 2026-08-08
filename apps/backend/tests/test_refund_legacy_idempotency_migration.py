"""Legacy app_refund UNIQUE(idempotency_key) → UNIQUE(organization_id, idempotency_key)."""

from __future__ import annotations

from datetime import datetime, timezone

import duckdb
import pytest


def _legacy_refund_ddl(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the exact legacy shape: inline global UNIQUE on idempotency_key."""
    conn.execute("DROP TABLE IF EXISTS app_refund")
    conn.execute("""
        CREATE TABLE app_refund (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL,
            payment_id       INTEGER NOT NULL,
            amount           DECIMAL(18,4) NOT NULL,
            currency         VARCHAR(3) NOT NULL,
            reason           VARCHAR,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            processed_at     TIMESTAMP,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            idempotency_key  VARCHAR NOT NULL UNIQUE,
            CHECK (status IN ('pending', 'processed', 'failed')),
            CHECK (amount > 0)
        )
    """)


def _seed_legacy_rows(conn: duckdb.DuckDBPyConnection) -> list[tuple]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        (1, 10, 100, "25.5000", "USD", "partial", "processed", now, now, now, "shared-key-a"),
        (2, 20, 200, "10.0000", "USD", None, "pending", None, now, now, "other-key-b"),
    ]
    for row in rows:
        conn.execute(
            """
            INSERT INTO app_refund (
                id, organization_id, payment_id, amount, currency, reason, status,
                processed_at, created_at, updated_at, idempotency_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            list(row),
        )
    return rows


def _global_unique_present(conn: duckdb.DuckDBPyConnection) -> bool:
    rows = conn.execute(
        """
        SELECT constraint_column_names
        FROM duckdb_constraints()
        WHERE table_name = 'app_refund' AND constraint_type = 'UNIQUE'
        """
    ).fetchall()
    for (cols,) in rows:
        names = [str(c).lower() for c in (cols or [])]
        if names == ["idempotency_key"]:
            return True
    return False


def test_legacy_global_unique_survives_guessed_drop_index(tmp_path):
    """Document why DROP INDEX with guessed names is insufficient."""
    conn = duckdb.connect(str(tmp_path / "guess.duckdb"))
    try:
        _legacy_refund_ddl(conn)
        assert _global_unique_present(conn)
        for index_name in (
            "idx_refund_idempotency_key",
            "app_refund_idempotency_key_key",
            "app_refund_idempotency_key_uq",
        ):
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")
        assert _global_unique_present(conn), "inline UNIQUE must remain after guessed DROP INDEX"
        _seed_legacy_rows(conn)
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO app_refund (
                    id, organization_id, payment_id, amount, currency, reason, status,
                    processed_at, created_at, updated_at, idempotency_key
                ) VALUES (3, 99, 300, 1.0, 'USD', NULL, 'pending', NULL, CURRENT_TIMESTAMP,
                          CURRENT_TIMESTAMP, 'shared-key-a')
                """
            )
    finally:
        conn.close()


def test_production_migration_rebuilds_org_scoped_unique_lossless_and_idempotent(tmp_path):
    from app.packages.billing.infrastructure.schema import _ensure_refund_idempotency

    conn = duckdb.connect(str(tmp_path / "mig.duckdb"))
    try:
        _legacy_refund_ddl(conn)
        seeded = _seed_legacy_rows(conn)
        assert _global_unique_present(conn)

        _ensure_refund_idempotency(conn)

        # Data preserved (amounts, statuses, keys, org ids).
        preserved = conn.execute(
            """
            SELECT id, organization_id, payment_id, CAST(amount AS VARCHAR), currency,
                   reason, status, idempotency_key
            FROM app_refund ORDER BY id
            """
        ).fetchall()
        assert len(preserved) == 2
        assert preserved[0][0] == seeded[0][0]
        assert preserved[0][1] == seeded[0][1]
        assert preserved[0][6] == "processed"
        assert preserved[0][7] == "shared-key-a"
        assert preserved[1][6] == "pending"
        assert preserved[1][7] == "other-key-b"
        assert not _global_unique_present(conn)

        # Same key allowed across organizations.
        conn.execute(
            """
            INSERT INTO app_refund (
                id, organization_id, payment_id, amount, currency, reason, status,
                processed_at, created_at, updated_at, idempotency_key
            ) VALUES (3, 99, 300, 1.0, 'USD', NULL, 'pending', NULL, CURRENT_TIMESTAMP,
                      CURRENT_TIMESTAMP, 'shared-key-a')
            """
        )
        assert (
            int(
                conn.execute(
                    "SELECT COUNT(*) FROM app_refund WHERE idempotency_key = 'shared-key-a'"
                ).fetchone()[0]
            )
            == 2
        )

        # Same key still rejected within one organization.
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO app_refund (
                    id, organization_id, payment_id, amount, currency, reason, status,
                    processed_at, created_at, updated_at, idempotency_key
                ) VALUES (4, 10, 400, 2.0, 'USD', NULL, 'pending', NULL, CURRENT_TIMESTAMP,
                          CURRENT_TIMESTAMP, 'shared-key-a')
                """
            )

        before_second = conn.execute(
            "SELECT id, organization_id, idempotency_key, status FROM app_refund ORDER BY id"
        ).fetchall()
        _ensure_refund_idempotency(conn)  # idempotent second pass
        after_second = conn.execute(
            "SELECT id, organization_id, idempotency_key, status FROM app_refund ORDER BY id"
        ).fetchall()
        assert after_second == before_second
        assert not _global_unique_present(conn)
    finally:
        conn.close()
