"""Test R1: Reporting schema — Spec 024."""

from app.core.database import using_write_conn
from app.packages.reporting.infrastructure.schema import REPORTING_TABLES


def test_reporting_tables_exist():
    with using_write_conn() as conn:
        for table in REPORTING_TABLES:
            row = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()
            assert row and int(row[0]) >= 1, f"missing {table}"
